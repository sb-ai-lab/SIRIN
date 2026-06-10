from enum import Enum
from typing import Callable

from sklearn.metrics import (
    accuracy_score,
    auc,
    f1_score,
    fbeta_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    average_precision_score
)


class LogLevel(Enum):
    DEBUG = 'debug'
    INFO = 'info'
    WARNING = 'warning'
    ERROR = 'error'
    CRITICAL = 'critical'


class ModelType(Enum):
    CAUSAL = 'causal'
    BASE = 'base'
    TOKEN_CLASSIFICATION = 'token_classification'
    SEQUENCE_CLASSIFICATION = 'sequence_classification'


class ModelAdapterType(Enum):
    HUGGINGFACE = 'hf'
    VLLM = 'vllm'
    OPENAI = 'openai'


class DetectionTaskType(Enum):
    HALLUCINATION_DETECTION = 'hallucination'
    QUERY_ANSWERABILITY = 'answerability'


class FeatureType(Enum):
    HIDDEN = 'hidden'
    ATTENTION = 'attention'
    LOOKBACK = 'lookback'
    LOGIT = 'logit'
    SUBLAYER = 'sublayer'
    TOKEN_UNCERTAINTY = 'token_uncertainty'
    SEQUENCE_UNCERTAINTY = 'sequence_uncertainty'


class SplitStrategy(Enum):
    SENTENCE = 'sentence'
    PARAGRAPH = 'paragraph'
    CHARACTER = 'character'
    LANGCHAIN = 'langchain'
    ATOMIC = 'atomic_facts'


class AggregationMethod(Enum):
    MEAN = 'mean'
    MAX = 'max'
    MIN = 'min'
    VOTE = 'vote'


class SideType(Enum):
    LEFT = 'left'
    RIGHT = 'right'
    INNER = 'inner'
    OUTER = 'outer'


class AggregationType(Enum):
    MICRO = 'micro'
    MACRO = 'macro'
    CONCAT = 'concat'


class DetectionLevel(Enum):
    TOKEN = 'token'
    SEQUENCE = 'sequence'
    CLAIM = 'claim'


class DataCollatorType(Enum):
    """Data collator types for model training.
    
    - TOKEN: For token-level classification with -100 padding mask
    - PADDING: For sequence-level classification with scalar labels
    """
    TOKEN = 'token'
    PADDING = 'padding'


class Phase(Enum):
    TRAIN = 'train'
    TEST = 'test'
    VAL = 'val'


class CompressionMethod(Enum):
    """Supported compression methods."""

    PCA = 'pca'
    UMAP = 'umap'
    NONE = 'none'


class ScalingMethod(Enum):
    """Supported scaling methods."""

    STANDARD = 'standard'  # Z-score normalization: (x - mean) / std
    MINMAX = 'minmax'  # Min-Max scaling: (x - min) / (max - min)
    ROBUST = 'robust'  # Robust scaling using median and IQR
    NONE = 'none'  # No scaling


class LmMetric(Enum):
    """Standard NLP evaluation metrics constants."""

    ROUGE_1 = 'rouge_1'
    ROUGE_2 = 'rouge_2'
    ROUGE_L = 'rouge_l'
    BLEU = 'bleu'
    TER = 'ter'

    BERT_SCORE = 'bert_score'
    BERT_SCORE_PRECISION = 'bert_score_precision'
    BERT_SCORE_RECALL = 'bert_score_recall'
    BERT_SCORE_F1 = 'bert_score_f1'
    METEOR = 'meteor'

    @classmethod
    def get_rouge_metrics(cls) -> list['LmMetric']:
        """Get all ROUGE-based metrics."""
        return [cls.ROUGE_1, cls.ROUGE_2, cls.ROUGE_L]

    @classmethod
    def get_bert_metrics(cls) -> list['LmMetric']:
        """Get all BERT-based metrics."""
        return [cls.BERT_SCORE_PRECISION, cls.BERT_SCORE_RECALL, cls.BERT_SCORE_F1]


class ClassificationMetric(Enum):
    ROC_AUC = 'roc_auc'
    F1 = 'f1'
    ACCURACY = 'accuracy'
    PR_AUC = 'pr_auc'
    PRECISION = 'precision'
    RECALL = 'recall'
    FBETA = 'fbeta'
    AP = 'average_precision'

    @staticmethod
    def get_metric_function(metric: str) -> Callable:
        def pr_auc(y, y_pred_score):
            precision, recall, _ = precision_recall_curve(y, y_pred_score)
            return auc(recall, precision)

        if metric == ClassificationMetric.ROC_AUC.value:
            return roc_auc_score
        elif metric == ClassificationMetric.F1.value:
            return f1_score
        elif metric == ClassificationMetric.ACCURACY.value:
            return accuracy_score
        elif metric == ClassificationMetric.PR_AUC.value:
            return pr_auc
        elif metric == ClassificationMetric.PRECISION.value:
            return precision_score
        elif metric == ClassificationMetric.RECALL.value:
            return recall_score
        elif metric == ClassificationMetric.FBETA.value:
            return fbeta_score
        elif metric == ClassificationMetric.AP.value:
            return average_precision_score
        else:
            raise NotImplementedError(f'Unsupported metric: {metric}')

    def __str__(self):
        return self.value

    def startswith(self, prefix):
        return self.value.startswith(prefix)
    
BASIC_METRICS = [
    ClassificationMetric.F1,
    ClassificationMetric.ROC_AUC,
    ClassificationMetric.ACCURACY,
    ClassificationMetric.PR_AUC,
    ClassificationMetric.PRECISION,
    ClassificationMetric.RECALL,
    ClassificationMetric.AP
]

class TokenLocation(Enum):
    ANS_END = 'answer_end'
    ANS_START = 'answer_start'
    ANS_MID = 'answer_middle'
    EOS = 'eos'
    N_TO_ANS_START = 'n_to_answer_start'
    N_TO_ANS_END = 'n_to_answer_end'
    SUBSTRING = 'substring'