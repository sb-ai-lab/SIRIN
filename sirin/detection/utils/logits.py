from typing import Tuple

import torch


def logits_to_probs_preds(
    logits: torch.Tensor, threshold: float
) -> Tuple[torch.Tensor, torch.Tensor]:
    num_classes = logits.shape[-1]
    if num_classes == 1:
        probs = torch.sigmoid(logits).squeeze(-1)
        preds = (probs > threshold).long()
        return probs, preds

    if num_classes == 2:
        probs = torch.softmax(logits, dim=-1)[..., 1]
        preds = (probs > threshold).long()
        return probs, preds

    probs = torch.softmax(logits, dim=-1)
    preds = torch.argmax(probs, dim=-1)
    return probs, preds
