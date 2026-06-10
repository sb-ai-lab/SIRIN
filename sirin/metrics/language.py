import functools
from typing import Any, Dict, Iterable, List

import numpy as np
import torch
import torch.multiprocessing as mp
from loguru import logger as lg
from tqdm import tqdm

try:
    import nltk
    from bert_score import BERTScorer
    from nltk.translate.bleu_score import SmoothingFunction, sentence_bleu
    from nltk.translate.meteor_score import meteor_score
    from sacrebleu.metrics import TER as ter_score

    nltk.download('wordnet', quiet=True)
    nltk.download('punkt', quiet=True)
    nltk.download('punkt_tab', quiet=True)

    _smoothing_function = SmoothingFunction().method1
    _tokenizer = nltk.tokenize.word_tokenize
except ImportError as e:
    _smoothing_function = None
    _tokenizer = None
    lg.warning(f"Failed to import: {e}")

from sirin.definitions import LmMetric
from sirin.models.detection import BertScoreConfig

mp.set_start_method('spawn', force=True)


@functools.lru_cache(maxsize=10000)
def tokenize(text: str) -> List[str]:
    """
    Tokenize a given text or dictionary of text fields.

    Args:
        text (Union[str, Dict[str, str]]): Text or dictionary containing text fields.

    Returns:
        List[str]: List of tokens.
    """
    return _tokenizer(text.lower())


def vectorized_rouge_n_score(
    candidates: List[List[str]], references: List[List[str]], n: int
) -> np.ndarray:
    """
    Calculate the ROUGE-N score between a list of candidates and a list of references.

    Args:
        candidates (List[List[str]]): A list of tokenized candidate texts. Each candidate text is represented as a list of tokens.
        references (List[List[str]]): A list of tokenized reference texts. Each reference text is represented as a list of tokens.
        n (int): The size of the n-grams to consider.

    Returns:
        np.ndarray: An array of ROUGE-N scores. The length of the array is equal to the number of candidates.

    Calculates the ROUGE-N score between each candidate and each reference using n-grams. The ROUGE-N score is the harmonic mean of the precision and recall at n-gram level.

    The candidate and reference texts are first tokenized into n-grams using the `get_ngrams` function. The number of common n-grams between each candidate and each reference is calculated. The recall, precision, and F1 score are then calculated using the common n-grams and the lengths of the candidate and reference n-grams.

    Note: This function uses the numpy library for array operations.
    """

    def get_ngrams(tokens, n):
        return set(tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1))

    candidate_ngrams = [get_ngrams(c, n) for c in candidates]
    reference_ngrams = [get_ngrams(r, n) for r in references]

    common_ngrams = np.array(
        [len(cand & ref) for cand, ref in zip(candidate_ngrams, reference_ngrams)]
    )
    candidate_counts = np.array([len(cand) for cand in candidate_ngrams])
    reference_counts = np.array([len(ref) for ref in reference_ngrams])

    recalls = np.divide(
        common_ngrams,
        reference_counts,
        out=np.zeros_like(common_ngrams, dtype=float),
        where=reference_counts != 0,
    )
    precisions = np.divide(
        common_ngrams,
        candidate_counts,
        out=np.zeros_like(common_ngrams, dtype=float),
        where=candidate_counts != 0,
    )

    denominator = recalls + precisions
    f1_scores = np.divide(
        2 * recalls * precisions,
        denominator,
        out=np.zeros_like(denominator),
        where=denominator != 0,
    )

    return f1_scores


def vectorized_rouge_l_score(
    candidates: List[List[str]], references: List[List[str]]
) -> np.ndarray:
    """
    Compute the ROUGE-L (Recall-Oriented Understudy for Gisting Evaluation) score between a list of candidate and reference texts.

    Args:
        candidates (List[List[str]]): A list of tokenized candidate texts. Each candidate text is represented as a list of tokens.
        references (List[List[str]]): A list of tokenized reference texts. Each reference text is represented as a list of tokens.

    Returns:
        np.ndarray: An array of ROUGE-L scores. The length of the array is equal to the number of candidates.

    Calculates the ROUGE-L score between each candidate and each reference. The ROUGE-L score is the harmonic mean of the precision and recall at the LCS (Longest Common Subsequence) level.

    The candidate and reference texts are first tokenized. The length of the LCS (Longest Common Subsequence) between each candidate and each reference is calculated. The recall, precision, and F1 score are then calculated using the LCS lengths and the lengths of the candidate and reference texts.

    Note: This function uses the numpy library for array operations.
    """

    def lcs_length(X, Y):
        """
        Compute the length of the longest common subsequence (LCS) between two sequences.

        Args:
            X (List[str]): First sequence.
            Y (List[str]): Second sequence.

        Returns:
            int: Length of the LCS.
        """
        m, n = len(X), len(Y)
        L = [[0] * (n + 1) for _ in range(m + 1)]
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if X[i - 1] == Y[j - 1]:
                    L[i][j] = L[i - 1][j - 1] + 1
                else:
                    L[i][j] = max(L[i - 1][j], L[i][j - 1])
        return L[m][n]

    lcs_lengths = np.array([lcs_length(c, r) for c, r in zip(candidates, references)])
    candidate_lengths = np.array([len(c) for c in candidates])
    reference_lengths = np.array([len(r) for r in references])

    recalls = np.divide(
        lcs_lengths,
        reference_lengths,
        out=np.zeros_like(lcs_lengths, dtype=float),
        where=reference_lengths != 0,
    )
    precisions = np.divide(
        lcs_lengths,
        candidate_lengths,
        out=np.zeros_like(lcs_lengths, dtype=float),
        where=candidate_lengths != 0,
    )

    denominator = recalls + precisions
    f1_scores = np.divide(
        2 * recalls * precisions,
        denominator,
        out=np.zeros_like(denominator),
        where=denominator != 0,
    )

    return f1_scores


def calculate_lm_metrics(
    metrics: Dict[LmMetric, Any],
    generations: Iterable[str],
    gold_answers: Iterable[List[str]],
) -> Dict[str, List[float]]:
    """
    Calculates various metrics specified in the configuration for the given dataset.

    Args:
        metrics: Dictionary mapping metrics to their configurations
        generations: Generated outputs
        gold_answers: Gold standard answers (list of possible references per generation)

    Returns:
        Dict[str, List[float]]: A dictionary containing the calculated scores for different metrics.
    """
    all_scores = {}

    # Pre-tokenize all texts
    tok_generations = [tokenize(g) for g in generations]
    tok_gold_answers = [[tokenize(a) for a in ans] for ans in gold_answers]

    # Track if BERTScore has been calculated
    bert_score_calculated = False

    for metric, config in tqdm(
        metrics.items(), desc="Calculating metrics"
    ):
        if metric == LmMetric.ROUGE_1:
            all_scores[metric.value] = vectorized_rouge_n_score(
                tok_generations, [g[0] for g in tok_gold_answers], 1
            )
        elif metric == LmMetric.ROUGE_2:
            all_scores[metric.value] = vectorized_rouge_n_score(
                tok_generations, [g[0] for g in tok_gold_answers], 2
            )
        elif metric == LmMetric.ROUGE_L:
            all_scores[metric.value] = vectorized_rouge_l_score(
                tok_generations, [g[0] for g in tok_gold_answers]
            )
        elif metric == LmMetric.BLEU:
            all_scores[metric.value] = np.array(
                [
                    sentence_bleu(refs, cand, smoothing_function=_smoothing_function)
                    for cand, refs in zip(tok_generations, tok_gold_answers)
                ]
            )
        elif metric == LmMetric.METEOR:
            all_scores[metric.value] = np.array(
                [
                    meteor_score(refs, cand)
                    for cand, refs in zip(tok_generations, tok_gold_answers)
                ]
            )
        elif metric == LmMetric.TER:
            ter = ter_score()
            all_scores[metric.value] = np.array(
                [
                    ter.corpus_score(
                        [' '.join(cand)], [' '.join(ref) for ref in refs]
                    ).score
                    / 10000
                    for cand, refs in zip(tok_generations, tok_gold_answers)
                ]
            )
        elif metric in LmMetric.get_bert_metrics() and not bert_score_calculated:
            # Calculate all BERTScore metrics at once
            bert_config: BertScoreConfig = config

            scorer = BERTScorer(
                model_type=bert_config.model_path,
                num_layers=1,
                batch_size=bert_config.batch_size,
                nthreads=bert_config.nthreads,
                all_layers=False,
                idf=False,
                device=bert_config.device
                if bert_config.device and torch.cuda.is_available()
                else 'cpu',
                lang=bert_config.lang,
                rescale_with_baseline=False,
            )

            P, R, F1 = [], [], []
            for cand, refs in tqdm(
                zip(tok_generations, tok_gold_answers),
                total=len(tok_generations),
                desc="Calculating BERTScore",
                disable=False,
            ):
                cand_str = " ".join(cand)
                refs_str = [" ".join(ref) for ref in refs]

                p_scores, r_scores, f1_scores = [], [], []
                for ref in refs_str:
                    try:
                        p, r, f1 = scorer.score([cand_str], [ref])
                    except RuntimeError as e:
                        lg.error(f"Error calculating BERTScore: {e}")
                        lg.error(f"Candidate: {cand_str}")
                        lg.error(f"Reference: {ref}")
                        raise
                    p_scores.append(p.item())
                    r_scores.append(r.item())
                    f1_scores.append(f1.item())

                P.append(max(p_scores))
                R.append(max(r_scores))
                F1.append(max(f1_scores))

            # Store all BERTScore metrics at once
            all_scores[LmMetric.BERT_SCORE_PRECISION.value] = P
            all_scores[LmMetric.BERT_SCORE_RECALL.value] = R
            all_scores[LmMetric.BERT_SCORE_F1.value] = F1

            bert_score_calculated = True

    return all_scores
