import gc
import os
from typing import Any, Dict, List, Optional, Tuple, Union

import torch
from huggingface_hub import login
from loguru import logger as lg
from transformers import (
    AutoModel,
    AutoModelForCausalLM,
    AutoModelForSequenceClassification,
    AutoModelForTokenClassification,
    AutoTokenizer,
    StoppingCriteria,
    StoppingCriteriaList,
)

from sirin.models.detection import ModelStates
from sirin.models.inference import HFConfig
from sirin.inference.adapters.base import ModelAdapterBase
from sirin.inference.batch_processing import batch_processor
from sirin.inference.token_locators import TokenLocatorBase
from sirin.definitions import (
    HF_TOKEN_ENV,
    ModelType,
)
from sirin.definitions import TorchDtype
from sirin.utils.config_manager import validate_hydra_config
from sirin.inference.model_manager import manage_active_model


class HfModelAdapter(ModelAdapterBase):
    """HuggingFace model implementation."""

    @validate_hydra_config
    def __init__(
        self,
        config: HFConfig,
        model: Any = None,
        tokenizer: Any = None,
    ):
        super().__init__(config, model, tokenizer)

    def _get_primary_device(self) -> Optional[str]:
        """Get the device where the input embedding lives.

        Inputs must be on the same device as ``model.get_input_embeddings()``
        for the first ``F.embedding`` call to succeed.
        """
        if hasattr(self, 'model') and self.model is not None:
            try:
                embed = self.model.get_input_embeddings()
                if embed is not None:
                    embed_device = next(embed.parameters()).device
                    return str(embed_device)
            except (StopIteration, AttributeError):
                pass

        if hasattr(self, 'config') and hasattr(self.config, 'device_map') and self.config.device_map is not None:
            dm = self.config.device_map
            if isinstance(dm, str):
                if dm.startswith('cuda:') or dm == 'cpu':
                    return dm
            elif isinstance(dm, dict) and dm:
                first_device = next(iter(dm.values()))
                if isinstance(first_device, int):
                    return f'cuda:{first_device}'
                if isinstance(first_device, str):
                    return first_device

        return self.device

    def load(
        self,
        model: Optional[Union[AutoModelForCausalLM, AutoModel]] = None,
        tokenizer: Optional[AutoTokenizer] = None,
    ):
        """Load HuggingFace model and tokenizer."""
        if self._is_loaded:
            lg.warning('Model already loaded')
            return

        if model and tokenizer:
            lg.info(f'Using of preloaded HuggingFace model and tokenizer.')
            self.model, self.tokenizer = model, tokenizer
            self.config = None
        else:
            self._authenticate()
            self.model, self.tokenizer = self._load_model_and_tokenizer()
            lg.info(f'Loaded HuggingFace model: {self.config.model_path}')

        # Only move to device if device_map is not used
        # When device_map is set, the model is already distributed across devices
        use_device_map = hasattr(self.config, 'device_map') and self.config.device_map is not None
        if self.device and not use_device_map:
            self.model = self.model.to(self.device)
        elif use_device_map:
            # Update device to primary device for input handling
            self.device = self._get_primary_device()
            lg.info(f'Using device_map, primary device for inputs: {self.device}')

        if not self.tokenizer.pad_token:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        self._is_loaded = True
        self._model_name = self.model.config.name_or_path

    def _authenticate(self):
        """Authenticate with HuggingFace Hub if token is available."""
        hf_token = os.environ.get(HF_TOKEN_ENV)
        if hf_token:
            login(token=hf_token)
        else:
            lg.warning(
                'No Hugging Face token found. Proceeding without login. '
                'This may limit access to some models.'
            )

    def _load_model_and_tokenizer(
        self,
    ) -> Tuple[Union[AutoModelForCausalLM, AutoModel], AutoTokenizer]:
        """Load model and tokenizer from HuggingFace."""
        model_kwargs = {}
        if hasattr(self.config, 'model_dtype') and self.config.model_dtype is not None:
            model_kwargs['dtype'] = TorchDtype.from_str(self.config.model_dtype)

        if hasattr(self.config, 'model_kwargs'):
            model_kwargs.update(self.config.model_kwargs)

        # Multi-GPU support via Accelerate device_map
        if hasattr(self.config, 'device_map') and self.config.device_map is not None:
            model_kwargs['device_map'] = self.config.device_map
            model_kwargs['low_cpu_mem_usage'] = getattr(self.config, 'low_cpu_mem_usage', True)
            if hasattr(self.config, 'max_memory') and self.config.max_memory is not None:
                model_kwargs['max_memory'] = self.config.max_memory
            if hasattr(self.config, 'offload_folder') and self.config.offload_folder is not None:
                model_kwargs['offload_folder'] = self.config.offload_folder
            lg.info(f'Using device_map={self.config.device_map} for multi-GPU model loading')

        if self.config.model_type == ModelType.CAUSAL:
            model = AutoModelForCausalLM.from_pretrained(
                self.config.model_path,
                attn_implementation=self.config.attn_implementation,
                **model_kwargs,
            )
        elif self.config.model_type == ModelType.BASE:
            model = AutoModel.from_pretrained(
                self.config.model_path,
                attn_implementation=self.config.attn_implementation,
                **model_kwargs,
            )
        elif self.config.model_type == ModelType.TOKEN_CLASSIFICATION:
            model = AutoModelForTokenClassification.from_pretrained(
                self.config.model_path,
                num_labels=self.config.num_labels,
                attn_implementation=self.config.attn_implementation,
                problem_type='single_label_classification',
                **model_kwargs,
            )
        elif self.config.model_type == ModelType.SEQUENCE_CLASSIFICATION:
            model = AutoModelForSequenceClassification.from_pretrained(
                self.config.model_path,
                num_labels=self.config.num_labels,
                attn_implementation=self.config.attn_implementation,
                problem_type='single_label_classification',
                **model_kwargs,
            )
        else:
            raise ValueError(f'Unsupported model type: {self.config.model_type}')

        tokenizer = AutoTokenizer.from_pretrained(
            getattr(self.config, 'tokenizer_path', None) or self.config.model_path,
        )
        
        if self.config.truncation:
            lg.warning("Due to unexpected behavior when truncating use `truncation=False`")

        if self.config.max_length is not None:
            tokenizer.max_length = min(self.config.max_length, tokenizer.model_max_length)

        if self.config.padding and self.config.padding_side != 'right':
            lg.warning("Due to unexpected behavior when padding, use `padding_side='right'` instead")
            tokenizer.padding = self.config.padding

        tokenizer.padding_side = self.config.padding_side or 'right'
        lg.info(f'Using padding_side={tokenizer.padding_side} for padding')

        return model, tokenizer

    def _get_stopping_criteria(self, stop_sequences: List[str]) -> StoppingCriteriaList:
        class StopSequenceCriteria(StoppingCriteria):
            def __init__(self, tokenizer, stop_sequences):
                self.tokenizer = tokenizer
                self.stop_ids = [
                    tokenizer.encode(seq, add_special_tokens=False)
                    for seq in stop_sequences
                ]

            def __call__(self, input_ids, scores, **kwargs):
                for stop_ids in self.stop_ids:
                    if input_ids[0, -len(stop_ids) :].tolist() == stop_ids:
                        return True
                return False

        return StoppingCriteriaList(
            [StopSequenceCriteria(self.tokenizer, stop_sequences)]
        )

    @manage_active_model
    @batch_processor(batch_size=None, flatten_results=True, log_progress=True)
    def sample(
        self,
        inputs: Union[List[str], List[List[Dict]]],
        max_tokens: int = 100,
        temperature: float = 1.0,
        top_p: float = 1.0,
        top_k: int = -1,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0,
        stop_sequences: Optional[List[str]] = None,
        padding: Union[str, bool] = False,
        truncation: bool = False,
        max_length: Optional[int] = None,
        return_logprobs: bool = False,
        top_logprobs: int = 1,
        num_return_sequences: int = 1,
        **kwargs: Any,
    ) -> Union[List[str], Tuple[List[str], List[List[List[Tuple[str, float]]]]]]:
        """Generate text using HuggingFace model with batch processing."""
        if not self._is_loaded:
            self.load()

        tokenized_inputs = self.tokenizer(
            self._preprocess_input(inputs),
            padding=padding or self.config.padding,
            truncation=truncation or self.config.truncation,
            max_length=max_length or self.tokenizer.max_length,
            return_tensors='pt',
            add_special_tokens=False, # not self.config.use_chat_template,
            return_token_type_ids=False,
        )
        # Use primary device for inputs (first device in device_map if using multi-GPU)
        input_device = self._get_primary_device()
        tokenized_inputs = tokenized_inputs.to(input_device)

        generation_kwargs = {
            'max_new_tokens': max_tokens,
            'temperature': temperature,
            'do_sample': temperature > 0,
            'pad_token_id': self.tokenizer.eos_token_id,
            'output_scores': return_logprobs,
            'return_dict_in_generate': return_logprobs,
            'num_return_sequences': num_return_sequences,
        }
        if top_p < 1.0:
            generation_kwargs['top_p'] = top_p
        if top_k > 0:
            generation_kwargs['top_k'] = top_k
        if frequency_penalty != 0.0:
            generation_kwargs['frequency_penalty'] = frequency_penalty
        if presence_penalty != 0.0:
            generation_kwargs['presence_penalty'] = presence_penalty
        if stop_sequences:
            generation_kwargs['stopping_criteria'] = self._get_stopping_criteria(
                stop_sequences
            )
        generation_kwargs.update(kwargs)

        with torch.no_grad():
            if return_logprobs:
                outputs = self.model.generate(**tokenized_inputs, **generation_kwargs)
                generated_sequences = outputs.sequences
                scores = outputs.scores
            else:
                generated_sequences = self.model.generate(**tokenized_inputs, **generation_kwargs)
                scores = None

        batch_size = len(inputs)
        responses = []
        
        input_lengths = tokenized_inputs['attention_mask'].sum(dim=1)
        
        for i in range(batch_size * num_return_sequences):
            generated_ids = generated_sequences[i, input_lengths[i // num_return_sequences]:]
            response = self.tokenizer.decode(generated_ids, skip_special_tokens=True)
            responses.append(response)

        if return_logprobs and scores is not None:
            logprobs_for_responses = []
            
            for input_idx in range(batch_size):
                input_logprobs = []
                for seq_idx in range(num_return_sequences):
                    seq_logprobs = []
                    input_logprobs.append(seq_logprobs)
                logprobs_for_responses.append(input_logprobs)
            
            for step, step_scores in enumerate(scores):
                probs = torch.softmax(step_scores, dim=-1)
                top_probs, top_indices = torch.topk(probs, min(top_logprobs, probs.size(-1)), dim=-1)
                
                top_logprobs_tensor = torch.log(top_probs + 1e-8)

                for batch_idx in range(batch_size * num_return_sequences):
                    input_idx = batch_idx // num_return_sequences
                    seq_idx = batch_idx % num_return_sequences
                    
                    top_tokens_logprobs = []
                    for j in range(top_indices.size(1)):
                        token_id = top_indices[batch_idx][j].item()
                        logprob = top_logprobs_tensor[batch_idx][j].item()
                        top_tokens_logprobs.append(logprob)
                    
                    logprobs_for_responses[input_idx][seq_idx].append(top_tokens_logprobs)
            
            return responses, logprobs_for_responses
        
        return responses

    @manage_active_model
    def probe_num_attention_layers(self) -> int:
        """Run a single dummy forward pass to count attention tensors.

        Hybrid-attention models (e.g. Qwen3.5) return fewer attention
        tensors than ``num_hidden_layers`` because only a subset of
        blocks use standard full attention.  This method returns the
        actual count so callers can choose valid layer indices.
        """
        if not self._is_loaded:
            self.load()

        dummy_input = self.tokenizer(
            'probe', return_tensors='pt', add_special_tokens=True,
        ).to(self._get_primary_device())

        with torch.no_grad():
            outputs = self.model(**dummy_input, output_attentions=True)

        return len(outputs.attentions)

    @manage_active_model
    def generate_hiddens(
        self,
        inputs: Union[List[str], List[List[Dict]]],
        return_attention: bool = False,
        return_hiddens: bool = True,
        return_logits: bool = False,
        return_sublayers: bool = False,
        layers: Optional[List[int]] = None,
        padding: Union[str, bool] = False,
        truncation: bool = False,
        max_length: Optional[int] = None,
        token_locator: Optional[Union[List[TokenLocatorBase], TokenLocatorBase]] = None,
        **kwargs: Any,
    ) -> ModelStates:
        """Generate hidden states and attention weights in batch."""
        if not self._is_loaded:
            self.load()
        
        # Tokenize all inputs at once with consistent padding
        # This ensures all batches will have the same shape for proper merging
        tokenized_inputs = self.tokenizer(
            self._preprocess_input(inputs),
            padding=padding or self.config.padding,
            truncation=truncation or self.config.truncation,
            max_length=max_length or self.tokenizer.max_length,
            return_tensors='pt',
            add_special_tokens=False, # not self.config.use_chat_template,
        )
        
        input_device = self._get_primary_device()
        tokenized_inputs = tokenized_inputs.to(input_device)
        
        # Store full tokenized_inputs for access in batched method
        self._full_tokenized_inputs = tokenized_inputs
        self._full_original_inputs = inputs
        self._batch_start_idx = 0
        
        return self._generate_hiddens_from_tokens(
            inputs=inputs,
            return_attention=return_attention,
            return_hiddens=return_hiddens,
            return_logits=return_logits,
            return_sublayers=return_sublayers,
            layers=layers,
            token_locator=token_locator,
            **kwargs,
        )
    
    @batch_processor(batch_size=None, flatten_results=True, log_progress=True)
    def _generate_hiddens_from_tokens(
        self,
        inputs: Union[List[str], List[List[Dict]]],
        return_attention: bool = False,
        return_hiddens: bool = True,
        return_logits: bool = False,
        return_sublayers: bool = False,
        layers: Optional[List[int]] = None,
        token_locator: Optional[Union[List[TokenLocatorBase], TokenLocatorBase]] = None,
        **kwargs: Any,
    ) -> ModelStates:
        """Generate hidden states from pre-tokenized inputs.
        
        This method is decorated with batch_processor which handles automatic batching
        and merging. It uses self._full_tokenized_inputs to slice the appropriate batch.
        
        Args:
            inputs: Original text inputs for this batch (batched by batch_processor)
        """
        # Get the batch slice from full tokenized inputs
        start_idx = self._batch_start_idx
        end_idx = start_idx + len(inputs)
        
        tokenized_inputs = {
            key: value[start_idx:end_idx]
            for key, value in self._full_tokenized_inputs.items()
        }
        
        # Update start index for next batch
        self._batch_start_idx = end_idx

        # sublayers handlers
        # Note: Forward hooks work with device_map, but need to ensure hooks are on correct device
        handles = []
        input_hiddens = []
        attention_output = []
        use_device_map = hasattr(self.model, 'hf_device_map') and self.model.hf_device_map is not None
        
        if return_sublayers:
            if use_device_map:
                lg.warning(
                    'Using forward hooks with device_map. Hooks will be registered on the device '
                    'where each layer is located. Ensure outputs are moved to CPU if needed.'
                )
            
            if layers:
                for layer_ in layers:
                    try:
                        input_handle = self.model.model.layers[
                            layer_
                        ].register_forward_pre_hook(
                            lambda m, i: input_hiddens.append(i[0].detach().cpu() if use_device_map else i[0].detach())
                        )
                        output_handle = self.model.model.layers[
                            layer_
                        ].self_attn.register_forward_hook(
                            lambda m, i, o: attention_output.append(o[0].detach().cpu() if use_device_map else o[0].detach())
                        )
                        handles.extend([input_handle, output_handle])
                    except Exception as e:
                        lg.warning(f'Failed to register hooks for layer {layer_}: {e}. Sublayers may not be extracted correctly.')
            else:
                try:
                    input_handle = self.model.model.layers[-1].register_forward_pre_hook(
                        lambda m, i: input_hiddens.append(i[0].detach().cpu() if use_device_map else i[0].detach())
                    )
                    output_handle = self.model.model.layers[-1].self_attn.register_forward_hook(
                        lambda m, i, o: attention_output.append(o[0].detach().cpu() if use_device_map else o[0].detach())
                    )
                    handles.extend([input_handle, output_handle])
                except Exception as e:
                    lg.warning(f'Failed to register hooks for last layer: {e}. Sublayers may not be extracted correctly.')

        with torch.no_grad():
            outputs = self.model(
                **tokenized_inputs,
                output_hidden_states=return_hiddens,
                output_attentions=return_attention,
            )
            logits = outputs.logits if return_logits else None

            # Process hidden states
            # When using device_map, outputs may be on different devices, so move to CPU
            all_hiddens = []
            if return_hiddens:
                hidden_states = outputs.hidden_states
                if layers:
                    # Move each hidden state to CPU (handles multi-device models)
                    selected_hidden = [hidden_states[i].cpu() if hasattr(hidden_states[i], 'device') else hidden_states[i] for i in layers]
                else:
                    last_hidden = hidden_states[-1]
                    selected_hidden = [last_hidden.cpu() if hasattr(last_hidden, 'device') else last_hidden]

                for i in range(len(inputs)):
                    seq_mask = tokenized_inputs['attention_mask'][i].bool().cpu()
                    # Always return tuple of layers
                    seq_hiddens = tuple(layer[i, seq_mask] for layer in selected_hidden)
                    all_hiddens.append(seq_hiddens)

            # Process attention weights
            # When using device_map, outputs may be on different devices, so move to CPU
            all_attentions = []
            if return_attention:
                attentions = outputs.attentions
                if layers:
                    # Move each attention to CPU (handles multi-device models)
                    n_attn = len(attentions)
                    attn_layers = [i for i in layers if -n_attn <= i < n_attn]
                    if len(attn_layers) < len(layers):
                        skipped = [i for i in layers if i not in attn_layers]
                        if not attn_layers:
                            raise ValueError(
                                f'All requested attention layers {layers} are out of range. '
                                f'Model returns only {n_attn} attention tensors '
                                f'(valid range: [-{n_attn}, {n_attn - 1}]). '
                                f'For hybrid-attention models, compute layer indices '
                                f'relative to the attention block count, not num_hidden_layers.'
                            )
                        lg.warning(
                            f'Model returned {n_attn} attention tensors, but layers={layers} were requested. '
                            f'Requested indices are applied to outputs.attentions (valid range: '
                            f'[-{n_attn}, {n_attn - 1}]), so indices {skipped} were skipped as out of range. '
                            f'In hybrid-attention models, outputs.attentions may include only the subset of '
                            f'blocks that use standard full attention.'
                        )
                    selected_attentions = [attentions[i].cpu() if hasattr(attentions[i], 'device') else attentions[i] for i in attn_layers]
                else:
                    last_attn = attentions[-1]
                    selected_attentions = [last_attn.cpu() if hasattr(last_attn, 'device') else last_attn]

                for i in range(len(inputs)):
                    seq_mask = tokenized_inputs['attention_mask'][i].bool().cpu()
                    # Always return tuple of layers
                    seq_attentions = tuple(
                        layer[i, :, seq_mask] for layer in selected_attentions
                    )
                    all_attentions.append(seq_attentions)

            # Generate locations if token_locator is available
            locations = []
            if token_locator is not None:
                token_locator_tokenized_inputs = self.tokenizer(
                    self._preprocess_input(inputs),
                    padding=False,
                    truncation=False,
                    add_special_tokens=False, # not self.config.use_chat_template,
                )
                if isinstance(token_locator, List):
                    for locator in token_locator:
                        location = self.locate_tokens(
                            locator,
                            inputs,
                            token_locator_tokenized_inputs,
                        )
                        locations.append(location)
                else:
                    locations = self.locate_tokens(
                        token_locator,
                        inputs,
                        token_locator_tokenized_inputs,
                    )

            all_sublayers = []
            if return_sublayers:
                sublayers = [
                    inp + attn for inp, attn in zip(input_hiddens, attention_output)
                ]
                for i in range(len(inputs)):
                    seq_mask = tokenized_inputs['attention_mask'][i].bool().cpu()
                    # Always return tuple of layers
                    seq_sublayers = tuple(layer[i, seq_mask] for layer in sublayers)
                    all_sublayers.append(seq_sublayers)

                for handle in handles:
                    handle.remove()

            result = ModelStates(
                hiddens=all_hiddens,
                attentions=all_attentions,
                locations=locations,
                logits=logits,
                sublayers=all_sublayers,
                masks=tokenized_inputs['attention_mask'].bool().cpu()
            )

            return result

    def locate_tokens(
        self,
        token_locator: TokenLocatorBase,
        inputs: Union[List[str], List[List[Dict]]],
        tokenized_inputs: Dict[str, Any],
    ) -> Optional[List[Dict]]:
        locations = []
        for i, sample in enumerate(inputs):
            # Extract answer from chat template if available
            answer = None
            if isinstance(sample, list) and len(sample) > 0:
                for j, msg in enumerate(sample):
                    if isinstance(msg, dict) and msg.get('role') == 'assistant':
                        answer = self._preprocess_input([sample])[0][len(self._preprocess_input([sample[:j]])[0]):]
                        break
            
            location = token_locator.locate(
                tokens=tokenized_inputs["input_ids"][i],
                tokenizer=self.tokenizer,
                answer_text=answer,
            )
            locations.append(location)
        return locations

    def unload(self):
        """Unload model and free GPU memory."""
        super().unload()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        gc.collect()
        lg.info('Unloaded HuggingFace model and freed memory')

    def _preprocess_input(self, inputs: Union[List[str], List[List[Dict]]]) -> str:
        formatted_prompts = []

        for input_item in inputs:
            if isinstance(input_item, str):
                formatted_tokens = self.tokenizer(
                    input_item,
                    padding=False,
                    truncation=False,
                    add_special_tokens=True,
                )
                formatted_string = self.tokenizer.decode(
                    formatted_tokens['input_ids'],
                    skip_special_tokens=False,
                )
            elif isinstance(input_item, list):
                if self.config.use_chat_template and self.tokenizer.chat_template:
                    formatted_string = self.tokenizer.apply_chat_template(
                        input_item,
                        tokenize=False,
                        add_generation_prompt=False,
                        padding=False,
                        truncation=False,
                    )
                else:
                    formatted_tokens = self.tokenizer(
                        *[role_item['content'] for role_item in input_item],
                        padding=False,
                        truncation=False,
                        add_special_tokens=True,
                    )
                    formatted_string = self.tokenizer.decode(
                        formatted_tokens['input_ids'],
                        skip_special_tokens=False,
                    )
            else:
                raise ValueError(f'Unsupported input fromat: {input_item}')

            formatted_prompts.append(formatted_string)

        return formatted_prompts
