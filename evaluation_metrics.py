"""
Evaluation Metrics Module
=========================
Computes BLEU and ROUGE-L scores to measure the quality of generated
compiler-error explanations against ground-truth reference texts.

Usage
-----
    from evaluation_metrics import EvaluationPipeline

    pipeline = EvaluationPipeline()

    # Single prediction
    score = pipeline.evaluate_single(prediction="…", reference="…")
    print(score)

    # Batch evaluation
    results = pipeline.evaluate_dataset(predictions=[…], references=[…])
    print(results.average_bleu, results.average_rouge_l)
"""

import re
import math
from collections import Counter
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple


# ──────────────────────────────────────────────────────────────────────────────
# Tokenisation helpers
# ──────────────────────────────────────────────────────────────────────────────

def _tokenize(text: str) -> List[str]:
    """
    Lightweight tokeniser: lower-case, keep alphanumeric tokens and
    single punctuation characters (helps capture code symbols).
    """
    return re.findall(r"[a-zA-Z0-9_]+|[^\s\w]", text.lower())


def _ngrams(tokens: List[str], n: int) -> List[Tuple[str, ...]]:
    return [tuple(tokens[i: i + n]) for i in range(len(tokens) - n + 1)]


# ──────────────────────────────────────────────────────────────────────────────
# BLEU
# ──────────────────────────────────────────────────────────────────────────────

def bleu_score(
    hypothesis: str,
    reference: str,
    max_n: int = 4,
    weights: Optional[List[float]] = None,
) -> float:
    """
    Compute sentence-level BLEU (1-gram to max_n-gram) with brevity penalty.

    Parameters
    ----------
    hypothesis  : generated text
    reference   : ground-truth text
    max_n       : maximum n-gram order (default 4 → BLEU-4)
    weights     : per-order weights; defaults to uniform (1/max_n each)

    Returns
    -------
    BLEU score in [0, 1]
    """
    if weights is None:
        weights = [1.0 / max_n] * max_n

    hyp_tokens = _tokenize(hypothesis)
    ref_tokens = _tokenize(reference)

    if not hyp_tokens:
        return 0.0

    # Brevity penalty
    bp = (
        1.0
        if len(hyp_tokens) >= len(ref_tokens)
        else math.exp(1 - len(ref_tokens) / len(hyp_tokens))
    )

    log_sum = 0.0
    for n, w in enumerate(weights, 1):
        hyp_ngrams = Counter(_ngrams(hyp_tokens, n))
        ref_ngrams = Counter(_ngrams(ref_tokens, n))

        if not hyp_ngrams:
            return 0.0

        clipped = sum(
            min(count, ref_ngrams[gram]) for gram, count in hyp_ngrams.items()
        )
        total = sum(hyp_ngrams.values())

        if total == 0 or clipped == 0:
            return 0.0

        log_sum += w * math.log(clipped / total)

    return bp * math.exp(log_sum)


# ──────────────────────────────────────────────────────────────────────────────
# ROUGE-L
# ──────────────────────────────────────────────────────────────────────────────

def _lcs_length(x: List[str], y: List[str]) -> int:
    """Dynamic-programming LCS length (memory-optimised 1-D DP)."""
    m, n = len(x), len(y)
    prev = [0] * (n + 1)
    for i in range(1, m + 1):
        curr = [0] * (n + 1)
        for j in range(1, n + 1):
            if x[i - 1] == y[j - 1]:
                curr[j] = prev[j - 1] + 1
            else:
                curr[j] = max(prev[j], curr[j - 1])
        prev = curr
    return prev[n]


def rouge_l_score(hypothesis: str, reference: str, beta: float = 1.2) -> float:
    """
    Compute ROUGE-L (F-measure based on LCS).

    Parameters
    ----------
    hypothesis : generated text
    reference  : ground-truth text
    beta       : F-measure trade-off (default 1.2 → slightly favour recall)

    Returns
    -------
    ROUGE-L F-score in [0, 1]
    """
    hyp_tokens = _tokenize(hypothesis)
    ref_tokens = _tokenize(reference)

    if not hyp_tokens or not ref_tokens:
        return 0.0

    lcs = _lcs_length(hyp_tokens, ref_tokens)
    precision = lcs / len(hyp_tokens)
    recall = lcs / len(ref_tokens)

    if precision + recall == 0:
        return 0.0

    f_score = (
        (1 + beta ** 2) * precision * recall
        / (beta ** 2 * precision + recall)
    )
    return f_score


# ──────────────────────────────────────────────────────────────────────────────
# ROUGE-1 (bag-of-words unigram, for reference)
# ──────────────────────────────────────────────────────────────────────────────

def rouge_1_score(hypothesis: str, reference: str) -> Dict[str, float]:
    """
    Compute ROUGE-1 precision, recall, and F1.
    """
    hyp_counts = Counter(_tokenize(hypothesis))
    ref_counts = Counter(_tokenize(reference))

    overlap = sum((hyp_counts & ref_counts).values())
    hyp_total = sum(hyp_counts.values())
    ref_total = sum(ref_counts.values())

    precision = overlap / hyp_total if hyp_total else 0.0
    recall = overlap / ref_total if ref_total else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )
    return {"precision": precision, "recall": recall, "f1": f1}


# ──────────────────────────────────────────────────────────────────────────────
# Result dataclasses
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class SingleScore:
    prediction: str
    reference: str
    bleu: float
    rouge_l: float
    rouge_1_f1: float

    def format(self) -> str:
        return (
            f"  BLEU    : {self.bleu:.4f}\n"
            f"  ROUGE-L : {self.rouge_l:.4f}\n"
            f"  ROUGE-1 : {self.rouge_1_f1:.4f}\n"
        )


@dataclass
class DatasetEvaluationResult:
    scores: List[SingleScore] = field(default_factory=list)
    average_bleu: float = 0.0
    average_rouge_l: float = 0.0
    average_rouge_1: float = 0.0

    def format_summary(self) -> str:
        lines = [
            "=" * 50,
            "EVALUATION SUMMARY",
            "=" * 50,
            f"  Samples evaluated : {len(self.scores)}",
            f"  Avg BLEU          : {self.average_bleu:.4f}",
            f"  Avg ROUGE-L       : {self.average_rouge_l:.4f}",
            f"  Avg ROUGE-1       : {self.average_rouge_1:.4f}",
            "=" * 50,
        ]
        return "\n".join(lines)

    def format_per_sample(self) -> str:
        lines = []
        for i, s in enumerate(self.scores, 1):
            lines.append(f"\n--- Sample {i} ---")
            lines.append(s.format())
        return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────────────────
# Evaluation Pipeline
# ──────────────────────────────────────────────────────────────────────────────

class EvaluationPipeline:
    """
    High-level interface for evaluating compiler-error explanations.

    Example
    -------
    >>> pipeline = EvaluationPipeline()
    >>> result = pipeline.evaluate_dataset(predictions, references)
    >>> print(result.format_summary())
    """

    def evaluate_single(
        self,
        prediction: str,
        reference: str,
    ) -> SingleScore:
        """Evaluate one prediction against one reference."""
        bleu = bleu_score(prediction, reference)
        rouge_l = rouge_l_score(prediction, reference)
        r1 = rouge_1_score(prediction, reference)
        return SingleScore(
            prediction=prediction,
            reference=reference,
            bleu=bleu,
            rouge_l=rouge_l,
            rouge_1_f1=r1["f1"],
        )

    def evaluate_dataset(
        self,
        predictions: List[str],
        references: List[str],
        verbose: bool = False,
    ) -> DatasetEvaluationResult:
        """
        Evaluate a list of predictions against ground-truth references.

        Parameters
        ----------
        predictions : list of generated explanation strings
        references  : list of ground-truth explanation strings (same order)
        verbose     : if True, print per-sample scores during evaluation

        Returns
        -------
        DatasetEvaluationResult with per-sample scores and averages
        """
        if len(predictions) != len(references):
            raise ValueError(
                f"Length mismatch: {len(predictions)} predictions vs "
                f"{len(references)} references."
            )

        scores: List[SingleScore] = []

        for i, (pred, ref) in enumerate(zip(predictions, references)):
            score = self.evaluate_single(pred, ref)
            scores.append(score)
            if verbose:
                print(f"Sample {i + 1}:")
                print(score.format())

        n = len(scores)
        avg_bleu = sum(s.bleu for s in scores) / n if n else 0.0
        avg_rouge_l = sum(s.rouge_l for s in scores) / n if n else 0.0
        avg_rouge_1 = sum(s.rouge_1_f1 for s in scores) / n if n else 0.0

        return DatasetEvaluationResult(
            scores=scores,
            average_bleu=avg_bleu,
            average_rouge_l=avg_rouge_l,
            average_rouge_1=avg_rouge_1,
        )

    def evaluate_from_dict(
        self,
        data: List[Dict[str, str]],
        pred_key: str = "prediction",
        ref_key: str = "reference",
        verbose: bool = False,
    ) -> DatasetEvaluationResult:
        """
        Evaluate from a list of dicts, each having 'prediction' and 'reference' keys.
        Useful when loading from JSON datasets.
        """
        predictions = [d[pred_key] for d in data]
        references = [d[ref_key] for d in data]
        return self.evaluate_dataset(predictions, references, verbose=verbose)


# ──────────────────────────────────────────────────────────────────────────────
# Self-test
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    pipeline = EvaluationPipeline()

    test_pairs = [
        {
            "prediction": (
                "You missed a semicolon at the end of the statement. "
                "In C, every statement must end with a semicolon."
            ),
            "reference": (
                "A semicolon is missing at the end of the line. "
                "C requires all statements to be terminated with a semicolon."
            ),
        },
        {
            "prediction": (
                "The variable 'count' was not declared in this scope. "
                "Make sure to declare it before use."
            ),
            "reference": (
                "Variable 'count' is undeclared. Declare it with int count = 0; "
                "before using it in the current scope."
            ),
        },
        {
            "prediction": (
                "Type mismatch: you are assigning a float to an int, "
                "which may lose precision."
            ),
            "reference": (
                "Incompatible types: cannot assign a float value to an int variable "
                "without an explicit cast."
            ),
        },
    ]

    print("=== Per-Sample Evaluation ===")
    result = pipeline.evaluate_from_dict(test_pairs, verbose=True)

    print("\n" + result.format_summary())
