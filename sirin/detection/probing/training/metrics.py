import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict


def soft_f1_loss(input, target, smooth=1e-6):
    input = torch.sigmoid(input)
    tp = torch.sum(input * target)
    fp = torch.sum(input * (1 - target))
    fn = torch.sum((1 - input) * target)

    precision = (tp + smooth) / (tp + fp + smooth)
    recall = (tp + smooth) / (tp + fn + smooth)

    f1 = 2 * (precision * recall) / (precision + recall + smooth)
    f1_loss = 1 - f1.mean()

    return f1_loss


def soft_precision(input, target, smooth=1e-6):
    input = torch.sigmoid(input)
    target = target.float()

    tp = torch.sum(input * target)
    fp = torch.sum(input * (1 - target))

    precision = (tp + smooth) / (tp + fp + smooth)
    precision_loss = 1 - precision.mean()

    return precision_loss


def fuzzy_f1(input, target, smooth=1e-6):
    input = torch.sigmoid(input)
    target = target.float()

    fuzzy_set = torch.minimum(input, target)

    f1_score = 2 * fuzzy_set / (target.sum() + input.sum() + smooth)
    f1_score = 1 - f1_score.mean()

    return f1_score


def balanced_f_score(input, target, betta=1.0, weight=0.5, smooth=1e-6):
    input = torch.sigmoid(input)
    tp = torch.sum(input * target)
    fp = torch.sum(input * (1 - target))
    fn = torch.sum((1 - input) * target)
    tn = torch.sum((1 - input) * (1 - target))

    precision_class1 = tp / (tp + fp + smooth)
    recall_class1 = tp / (tp + fn + smooth)
    precision_class0 = tn / (tn + fn + smooth)
    recall_class0 = tn / (tn + fp + smooth)

    soft_f_class1 = (
        (1 + betta**2)
        * precision_class1
        * recall_class1
        / (betta**2 * precision_class1 + recall_class1 + smooth)
    )
    soft_f_class0 = (
        (1 + betta**2)
        * precision_class0
        * recall_class0
        / (betta**2 * precision_class0 + recall_class0 + smooth)
    )
    cost_class1 = 1 - soft_f_class1
    cost_class0 = 1 - soft_f_class0
    cost = weight * cost_class1 + (1 - weight) * cost_class0
    macro_cost = torch.mean(cost)

    return macro_cost


class FuzzyF1(nn.Module):
    def __init__(self, smooth=1e-6):
        super().__init__()
        self.smooth = smooth

    def forward(self, input, target):
        return fuzzy_f1(input, target, self.smooth)


class SoftPrecisionLoss(nn.Module):
    def __init__(self, smooth=1e-6):
        super().__init__()
        self.smooth = smooth

    def forward(self, input, target):
        return soft_precision(input, target, self.smooth)


class BalancedFScore(nn.Module):
    def __init__(self, betta=1.0, weight=0.5, smooth=1e-6):
        super().__init__()
        self.betta = betta
        self.weight = weight
        self.smooth = smooth

    def forward(self, input, target):
        return balanced_f_score(input, target, self.betta, self.weight, self.smooth)


class SupervisedContrastiveLoss(nn.Module):
    def __init__(self, temperature=0.07):
        super().__init__()
        self.temperature = temperature

    def forward(self, features, labels):
        device = features.device
        batch_size = features.shape[0]

        features = F.normalize(features, dim=1)

        sim = torch.mm(features, features.T)
        sim = sim / self.temperature

        labels = labels.view(-1, 1)
        pos_mask = (labels == labels.T).float()
        pos_mask.fill_diagonal_(0)

        log_prob = F.log_softmax(sim, dim=1)

        log_prob = log_prob * (1 - torch.eye(batch_size, device=device))

        pos_count = pos_mask.sum(dim=1, keepdim=True)
        pos_count = torch.clamp(pos_count, min=1.0)

        loss = -(log_prob * pos_mask).sum(dim=1) / pos_count.squeeze(1)
        loss = loss.mean()

        return loss


def compute_contrastive_metrics(
    features: torch.Tensor, labels: torch.Tensor, normalize: bool = True
) -> Dict[str, float]:
    """
    Computes quality metrics for contrastive learning embeddings.

    Args:
        features: Tensor of shape (batch_size, feature_dim) - embeddings
        labels: Tensor of shape (batch_size,) - class labels
        normalize: Whether to normalize features (set False if already normalized)

    Returns:
        Dictionary with metrics:
            - intra_class_distance: average distance within class
            - inter_class_distance: average distance between classes
            - separation_ratio: inter/intra ratio (higher = better)
            - alignment: alignment of embeddings with labels
            - uniformity: uniformity of embedding distribution
    """
    device = features.device
    batch_size = features.shape[0]

    # Normalize features if needed
    if normalize:
        features = F.normalize(features, dim=1)

    # Compute distance matrix
    dist_matrix = torch.cdist(features, features, p=2)

    # Create masks
    labels = labels.view(-1, 1)
    pos_mask = (labels == labels.T).float()
    neg_mask = (labels != labels.T).float()
    pos_mask.fill_diagonal_(0)

    # Intra-class distance (average distance between examples of the same class)
    if pos_mask.sum() > 0:
        intra_class_dist = (dist_matrix * pos_mask).sum() / pos_mask.sum()
    else:
        intra_class_dist = torch.tensor(0.0)

    # Inter-class distance (average distance between examples of different classes)
    if neg_mask.sum() > 0:
        inter_class_dist = (dist_matrix * neg_mask).sum() / neg_mask.sum()
    else:
        inter_class_dist = torch.tensor(0.0)

    # Separation ratio
    if intra_class_dist > 0:
        separation_ratio = inter_class_dist / intra_class_dist
    else:
        separation_ratio = torch.tensor(0.0)

    # Alignment: measures how close embeddings of the same class are to each other
    # Use negative average cosine similarity for positive pairs
    sim_matrix = torch.mm(features, features.T)
    if pos_mask.sum() > 0:
        alignment = -(sim_matrix * pos_mask).sum() / pos_mask.sum()
    else:
        alignment = torch.tensor(0.0)

    # Uniformity: measures uniformity of embedding distribution on hypersphere
    # Use average log of negative distance between all pairs
    sq_dists = torch.pow(dist_matrix, 2)
    uniformity = torch.log(torch.exp(-2 * sq_dists).sum()) - torch.log(
        torch.tensor(batch_size * (batch_size - 1), dtype=torch.float32)
    )

    return {
        "intra_class_distance": intra_class_dist.item(),
        "inter_class_distance": inter_class_dist.item(),
        "separation_ratio": separation_ratio.item(),
        "alignment": alignment.item(),
        "uniformity": uniformity.item(),
    }


def compute_hard_negative_stats(
    features: torch.Tensor, labels: torch.Tensor, threshold: float = 0.7
) -> Dict[str, float]:
    """
    Computes statistics for hard negatives.

    Args:
        features: Tensor of shape (batch_size, feature_dim)
        labels: Tensor of shape (batch_size,)
        threshold: similarity threshold for determining hard negatives

    Returns:
        Dictionary with statistics:
            - hard_negative_ratio: ratio of hard negatives among all negative pairs
            - avg_hard_negative_similarity: average similarity for hard negatives
            - max_hard_negative_similarity: maximum similarity for hard negatives
    """
    # Normalize features
    features = F.normalize(features, dim=1)

    # Compute similarity matrix
    sim_matrix = torch.mm(features, features.T)

    # Create masks
    labels = labels.view(-1, 1)
    neg_mask = (labels != labels.T).float()

    # Find hard negatives (high similarity but different class)
    neg_sims = sim_matrix * neg_mask
    hard_neg_mask = (neg_sims > threshold) * neg_mask

    # Compute statistics
    total_negatives = neg_mask.sum()
    hard_negatives = hard_neg_mask.sum()

    if total_negatives > 0:
        hard_negative_ratio = (hard_negatives / total_negatives).item()
    else:
        hard_negative_ratio = 0.0

    if hard_negatives > 0:
        hard_neg_sims = neg_sims[hard_neg_mask > 0]
        avg_hard_negative_similarity = hard_neg_sims.mean().item()
        max_hard_negative_similarity = hard_neg_sims.max().item()
    else:
        avg_hard_negative_similarity = 0.0
        max_hard_negative_similarity = 0.0

    return {
        "hard_negative_ratio": hard_negative_ratio,
        "avg_hard_negative_similarity": avg_hard_negative_similarity,
        "max_hard_negative_similarity": max_hard_negative_similarity,
    }
