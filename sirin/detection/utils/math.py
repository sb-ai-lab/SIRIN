import numpy as np
import torch


def split_entropy(
    entropy, thres=0.0
):  # 0.0 means even splits for normalized entropy scores
    """Binarize entropy scores into 0s and 1s"""
    binary_entropy = torch.full_like(entropy, -1, dtype=torch.float)
    binary_entropy[entropy < thres] = 0
    binary_entropy[entropy >= thres] = 1

    return binary_entropy


def binarize_entropy(entropy):
    split = best_split(entropy)
    
    return split_entropy(entropy, split), split


def best_split(entropy: torch.Tensor):
    """
    Identify best split for minimizing reconstruction error via low and high SE mean estimates,
    as discussed in Section 4. Binarization of paper (ArXiv: 2406.15927)
    """
    ents = entropy.numpy()
    ents = ents[ents < np.quantile(ents, 0.98)]
    splits = np.linspace(1e-10, ents.max(), 100)
    split_mses = []

    for split in splits:
        low_idxs, high_idxs = ents < split, ents >= split
        low_mean = np.mean(ents[low_idxs])
        high_mean = np.mean(ents[high_idxs])

        mse = np.sum((ents[low_idxs] - low_mean) ** 2) + np.sum(
            (ents[high_idxs] - high_mean) ** 2
        )
        mse = np.sum(mse)
        split_mses.append(mse)

    split_mses = np.array(split_mses)
    
    return splits[np.argmin(split_mses)]
