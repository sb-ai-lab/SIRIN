from pathlib import Path
from types import SimpleNamespace

import pytest
import torch
from torch.utils.data import DataLoader, TensorDataset

from sirin.detection.judging.judges.token.decoder import TokenDecoderJudge
from sirin.detection.judging.judges.utils import (
    SpanAlignmentError,
    align_span_annotation,
)
from sirin.detection.processors.saver import LayerFeatureCacheSaver
from sirin.models.detection import DetectorBaseConfig, HfJudgeConfig, TrainingArgsConfig, TrainingHistory
from sirin.detection.probing.training.trainers import HiddenStatesClassifierTrainerBase
from sirin.utils.savers import BatchCheckpointSaver
from sirin.inference.adapters.hf_adapter import _decode_generated, _state_forward_kwargs


@pytest.mark.parametrize('space', [' ', '\t', '\n', '\u00a0', '\u2003'])
def test_whitespace_alignment_recovers_glued_words(space):
    result = align_span_annotation(
        'A[SPAN]cat[/SPAN].', f'A{space}cat.', 'whitespace_only'
    )
    assert len(result.char_scores) == len(f'A{space}cat.')
    assert result.status == 'whitespace_recovered'
    # The missing separator straddles the span boundary and is therefore outside.
    assert result.char_scores[1] == 0.0


def test_whitespace_inside_one_span_is_recovered_inside():
    result = align_span_annotation(
        '[SPAN]bluecat[/SPAN]', 'blue cat', 'whitespace_only'
    )
    assert result.char_scores == [1.0] * len('blue cat')


def test_missing_whitespace_between_distinct_spans_is_outside():
    result = align_span_annotation(
        '[SPAN]blue[/SPAN][SPAN]cat[/SPAN]', 'blue cat', 'whitespace_only'
    )
    assert result.char_scores[len('blue')] == 0.0


@pytest.mark.parametrize(
    'generated,reason',
    [
        ('[SPAN]cat', 'malformed_tags'),
        ('[/SPAN]cat', 'malformed_tags'),
        ('[SPAN]a[SPAN]b[/SPAN][/SPAN]', 'malformed_tags'),
        ('A dog.', 'lexical_rewrite'),
        ('a cat.', 'lexical_rewrite'),
    ],
)
def test_alignment_rejects_malformed_or_lexically_changed_output(generated, reason):
    with pytest.raises(SpanAlignmentError) as caught:
        align_span_annotation(generated, 'A cat.', 'whitespace_only')
    assert caught.value.reason == reason


def test_alignment_handles_repeated_words_emoji_and_combining_characters():
    reference = 'same same 👩\u200d💻 cafe\u0301'
    generated = 'same [SPAN]same 👩\u200d💻[/SPAN] cafe\u0301'
    result = align_span_annotation(generated, reference, 'strict')
    assert len(result.char_scores) == len(reference)
    assert sum(result.char_scores) == len('same 👩\u200d💻')


class _Tokenizer:
    def __init__(self):
        self.additional_special_tokens = []
        self.all_special_tokens = ['<eos>']
        self.size = 10

    def __len__(self):
        return self.size

    def add_special_tokens(self, mapping):
        added = 0
        for token in mapping['additional_special_tokens']:
            if token not in self.additional_special_tokens:
                self.additional_special_tokens.append(token)
                self.all_special_tokens.append(token)
                self.size += 1
                added += 1
        return added


class _Model:
    def __init__(self):
        self.resized = []

    def resize_token_embeddings(self, size):
        self.resized.append(size)


def _untrained_decoder(peft_config=None):
    judge = object.__new__(TokenDecoderJudge)
    judge.config = HfJudgeConfig(peft_config=peft_config)
    judge.model_adapter = SimpleNamespace(tokenizer=_Tokenizer(), model=_Model())
    return judge


def test_untrained_decoder_does_not_mutate_tokenizer():
    judge = _untrained_decoder()
    assert not judge._uses_trained_span_markers
    assert len(judge.model_adapter.tokenizer) == 10
    assert judge.model_adapter.model.resized == []


def test_training_registers_markers_once_and_resizes_once():
    judge = _untrained_decoder()
    judge._prepare_trainable_span_markers()
    judge._prepare_trainable_span_markers()
    assert judge._uses_trained_span_markers
    assert judge.model_adapter.tokenizer.additional_special_tokens == ['[SPAN]', '[/SPAN]']
    assert judge.model_adapter.model.resized == [12]


def test_lora_training_preserves_embedding_and_lm_head_modules(monkeypatch):
    peft_config = SimpleNamespace(modules_to_save=['existing'])
    judge = _untrained_decoder(peft_config)
    wrapped = SimpleNamespace(wrapped=True)
    monkeypatch.setattr(
        'sirin.detection.judging.judges.token.decoder.get_peft_model',
        lambda model, config: wrapped,
    )
    judge._prepare_trainable_span_markers()
    assert peft_config.modules_to_save == ['embed_tokens', 'existing', 'lm_head']
    assert judge.model_adapter.model is wrapped


def test_feature_cache_is_identity_scoped_atomic_and_verified(tmp_path):
    one = LayerFeatureCacheSaver('org/model', str(tmp_path), identity={'revision': 'one'})
    two = LayerFeatureCacheSaver('org/model', str(tmp_path), identity={'revision': 'two'})
    assert one.cache_base_dir != two.cache_base_dir

    sample = [{'role': 'assistant', 'content': 'answer'}]
    one.save_layer_features(sample, 0, torch.tensor([[1.0]]))
    cached = one.load_layer_features(sample, 0, 'hidden')
    assert cached is not None
    assert cached.features.tolist() == [[1.0]]

    path = one.get_layer_cache_path(one.get_sample_hash(sample), 0, 'hidden')
    path.write_bytes(path.read_bytes() + b'corrupt')
    assert one.load_layer_features(sample, 0, 'hidden') is None


def test_batch_checkpoint_rejects_corruption_and_identity_mismatch(tmp_path):
    saver = BatchCheckpointSaver('data', 'model', str(tmp_path), computation_identity={'seed': 42})
    saver.save_checkpoint(0, 1, predictions=[1, 2])
    path = Path(tmp_path) / 'checkpoint_0_1.pkl'
    assert saver.load_single_checkpoint(path)['predictions'] == [1, 2]

    other = BatchCheckpointSaver('data', 'model', str(tmp_path), computation_identity={'seed': 43})
    with pytest.raises(RuntimeError, match='identity'):
        other.load_single_checkpoint(path)

    path.write_bytes(path.read_bytes() + b'corrupt')
    with pytest.raises(RuntimeError, match='checksum'):
        saver.load_single_checkpoint(path)


def test_hidden_only_qwen_style_forward_limits_logits_without_affecting_other_models():
    class QwenStyle:
        def forward(self, input_ids=None, logits_to_keep=0, **kwargs):
            pass

    class EncoderStyle:
        def forward(self, input_ids=None, **kwargs):
            pass

    hidden_only = _state_forward_kwargs(
        QwenStyle(), return_hiddens=True, return_attention=False, return_logits=False
    )
    with_logits = _state_forward_kwargs(
        QwenStyle(), return_hiddens=True, return_attention=False, return_logits=True
    )
    encoder = _state_forward_kwargs(
        EncoderStyle(), return_hiddens=True, return_attention=False, return_logits=False
    )
    assert hidden_only['logits_to_keep'] == 1
    assert 'logits_to_keep' not in with_logits
    assert 'logits_to_keep' not in encoder


def test_trained_marker_decode_keeps_span_tags_but_removes_chat_specials():
    class Tokenizer:
        all_special_tokens = ['<bos>', '<eos>', '[SPAN]', '[/SPAN]']

        def decode(self, ids, skip_special_tokens, clean_up_tokenization_spaces):
            if skip_special_tokens:
                return 'Acat.'
            return '<bos>A[SPAN]cat[/SPAN].<eos>'

    assert _decode_generated(
        Tokenizer(), [1], ['[SPAN]', '[/SPAN]']
    ) == 'A[SPAN]cat[/SPAN].'


def test_probe_training_state_is_atomic_verified_and_identity_bound(tmp_path):
    class ConcreteTrainer(HiddenStatesClassifierTrainerBase):
        def _setup_additional_loss_fn(self, cfg):
            pass

        def _setup_alpha_scheduler(self, cfg):
            pass

        def _setup_optimizer(self, cfg, model):
            pass

        def _setup_scheduler(self, cfg, model):
            pass

        def train_epoch(self, model, train_data, device):
            return 0.0

        def _evaluation_step(self, model, batch, device, compute_loss=False):
            return None

    trainer = ConcreteTrainer()
    model = torch.nn.Linear(2, 1)
    trainer.optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
    trainer.scheduler = None
    trainer.alpha_scheduler = None
    detector = SimpleNamespace(
        model=model,
        config=DetectorBaseConfig(model_save_path=str(tmp_path), device='cpu'),
    )
    data = DataLoader(TensorDataset(torch.zeros(2, 2), torch.zeros(2)), batch_size=1)
    cfg = TrainingArgsConfig(
        device='cpu', checkpoint_dir=str(tmp_path), checkpoint_interval_epochs=1
    )
    trainer._save_training_state(
        cfg, detector, data, None, 1, TrainingHistory(epochs=[1]), 0.7, [0.2]
    )
    cfg.resume_from_checkpoint = True
    epoch, history, metric, losses = trainer._load_training_state(
        cfg, detector, data, None
    )
    assert (epoch, history.epochs, metric, losses) == (1, [1], 0.7, [0.2])

    changed = DataLoader(TensorDataset(torch.zeros(3, 2), torch.zeros(3)), batch_size=1)
    with pytest.raises(RuntimeError, match='identity'):
        trainer._load_training_state(cfg, detector, changed, None)
