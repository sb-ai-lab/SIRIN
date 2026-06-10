from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from loguru import logger as lg
from torch.optim import LBFGS, Adam
from torch.optim.lr_scheduler import CyclicLR, ReduceLROnPlateau
from torch.utils.data import DataLoader
from tqdm import tqdm

from sirin.detection.probing.training import metrics, schedulers
from sirin.metrics import calculate_classification_metrics
from sirin.definitions import Phase, OFFSETS_COL, TARGET_COL
from sirin.detection.utils.basic import calibrate_threshold
from sirin.models.detection import DetectionResult, TrainingHistory, TrainingArgsConfig
from sirin.detection.splitters import SplitManager


class HiddenStatesClassifierTrainerBase(ABC):
    def __init__(self, context_splitter: Optional[SplitManager] = None):
        self._context_splitter = context_splitter
        self.optimizer: Optional[torch.optim.Optimizer] = None
        self.scheduler: Optional[torch.optim.lr_scheduler._LRScheduler] = None
        self.alpha_scheduler: Optional[schedulers.ExponentialAlphaScheduler] = None
        self.contrastive_loss_fn: Optional[metrics.SupervisedContrastiveLoss] = None
        self.threshold: float = 0.5
        self.problem_type: str = 'binary'  # 'binary', 'multiclass'
        self.use_contrastive: bool = False
        self.contrastive_weight: float = 0.5
        self.contrastive_temperature: float = 0.07
        self.zero_bce: bool = False

    def train(
        self,
        cfg: TrainingArgsConfig,
        detector: Any,
        train_data: DataLoader,
        val_data: Optional[DataLoader],
        group_ids: Optional[List[int]] = None,
        logger: Any = None,
    ) -> DetectionResult:
        self.threshold = cfg.threshold
        self.use_contrastive = (
            cfg.use_contrastive if hasattr(cfg, 'use_contrastive') else False
        )
        self.contrastive_weight = (
            cfg.contrastive_weight if hasattr(cfg, 'contrastive_weight') else 0.5
        )
        self.contrastive_temperature = (
            cfg.contrastive_temperature
            if hasattr(cfg, 'contrastive_temperature')
            else 0.07
        )
        self.zero_bce = cfg.zero_bce if hasattr(cfg, 'zero_bce') else False

        self._setup_optimizer(cfg, detector.model)
        self._setup_scheduler(cfg, detector.model)
        self._setup_alpha_scheduler(cfg)
        self._setup_additional_loss_fn(cfg)

        # Setup contrastive loss if needed
        if self.use_contrastive:
            self._setup_contrastive_loss(cfg)

        self.logger = logger

        best_metric = None
        target_metric = cfg.target_metric or 'f_beta'
        best_checkpoint = None
        loss_history = []

        history = TrainingHistory()

        lg.info(f'Starting training for {cfg.max_epochs} epochs.')
        for epoch in range(cfg.max_epochs):
            detector.model.to(cfg.device)
            detector.model.train()

            epoch_result = self.train_epoch(detector.model, train_data, cfg.device)

            # Handle both old (float) and new (dict) return formats
            if isinstance(epoch_result, dict):
                avg_loss = epoch_result['total_loss']
                if self.use_contrastive and 'cls_loss' in epoch_result:
                    history.contrastive.setdefault('train_cls_loss', []).append(float(epoch_result['cls_loss']))
                    history.contrastive.setdefault('train_contrastive_loss', []).append(float(epoch_result['contrastive_loss']))
            else:
                avg_loss = epoch_result

            loss_history.append(avg_loss)
            history.train_loss.append(float(avg_loss))
            history.epochs.append(epoch + 1)

            epoch_log: Dict[str, float] = {'train_loss': float(avg_loss)}
            if self.use_contrastive and isinstance(epoch_result, dict) and 'cls_loss' in epoch_result:
                epoch_log['train_cls_loss'] = float(epoch_result['cls_loss'])
                epoch_log['train_contrastive_loss'] = float(epoch_result['contrastive_loss'])

            if self.optimizer:
                lr = float(self.optimizer.param_groups[0]['lr'])
                history.learning_rate.append(lr)
                epoch_log['learning_rate'] = lr

            if self.logger:
                self.logger.log_metrics(epoch_log, epoch + 1, prefix='/train')

            if epoch > 0:
                loss_diff = abs(loss_history[-2] - loss_history[-1])
                if loss_diff < 1e-4:
                    lg.info('Early stopping due to small improvement.')
                    break

            lg.info(f'Epoch {epoch + 1}/{cfg.max_epochs} Loss: {avg_loss:.4f}')
            
            # Log contrastive metrics if enabled
            if self.use_contrastive and getattr(cfg, 'log_contrastive_metrics', True):
                contrastive_metrics = self._compute_and_log_contrastive_metrics(
                    detector.model, train_data, cfg.device, epoch
                )
                if contrastive_metrics:
                    for key, value in contrastive_metrics.items():
                        history.contrastive.setdefault(key, []).append(float(value))
                    if self.logger:
                        self.logger.log_metrics(contrastive_metrics, epoch + 1, prefix='/contrastive')

            if val_data and epoch % cfg.validation_interval == 0:
                val_result = self.evaluate(
                    detector.model,
                    val_data,
                    cfg.metrics,
                    cfg.device,
                    cfg.beta,
                    group_ids=group_ids,
                    compute_loss=True,
                )
                current_metric = (val_result.metrics or {}).get(target_metric, 0)

                if val_result.metrics:
                    history.val_epochs.append(epoch + 1)
                    for metric_name, metric_value in val_result.metrics.items():
                        history.val_metrics.setdefault(metric_name, []).append(float(metric_value))

                if self.logger and val_result.metrics:
                    self.logger.log_metrics(val_result.metrics, epoch + 1, prefix='/train')
                if best_metric is None or current_metric > best_metric:
                    best_metric = current_metric
                    if detector.config.model_save_path:
                        best_checkpoint = detector.save()
                        lg.info(
                            f'New best {target_metric}: {best_metric:.4f}. Checkpoint saved.'
                        )

            if self.scheduler is not None:
                if self.contrastive_loss_fn:
                    self.scheduler.step(avg_loss)
                else:
                    self.scheduler.step()
            if self.alpha_scheduler is not None:
                self.alpha_scheduler.step()

        lg.info(
            f'Training is over. Best validation results: {target_metric}={best_metric}.'
        )

        if best_checkpoint is not None:
            detector.load(detector.model_save_path)
        elif detector.config.model_save_path:
            best_checkpoint = detector.save()

        lg.info('Final train results:')
        train_results = self.evaluate(
            detector.model,
            val_data if val_data else train_data,
            cfg.metrics,
            cfg.device,
            cfg.beta,
            optimize=True,
            group_ids=group_ids,
        )
        lg.info(train_results.metrics)

        return DetectionResult(
            metrics=train_results.metrics,
            probs=train_results.probs,
            threshold=self.threshold,
            history=history,
        )

    def _setup_contrastive_loss(self, cfg: TrainingArgsConfig):
        """Setup contrastive loss function based on configuration."""
        loss_type = getattr(cfg, 'contrastive_loss_type', 'supervised')
        
        if loss_type != 'supervised':
            lg.warning(f"Contrastive loss type '{loss_type}' is no longer supported. Using supervised.")
        self.contrastive_loss_fn = metrics.SupervisedContrastiveLoss(
            temperature=self.contrastive_temperature,
        )
        lg.info(f'Using Supervised Contrastive Loss (temperature={self.contrastive_temperature})')

    @abstractmethod
    def _setup_alpha_scheduler(self, cfg: TrainingArgsConfig):
        pass

    @abstractmethod
    def _setup_additional_loss_fn(self, cfg: TrainingArgsConfig):
        pass

    @abstractmethod
    def _setup_optimizer(self, cfg: TrainingArgsConfig, model: nn.Module):
        pass

    @abstractmethod
    def _setup_scheduler(self, cfg: TrainingArgsConfig, model: nn.Module):
        pass

    @abstractmethod
    def train_epoch(
        self, model: nn.Module, train_data: DataLoader, device: str
    ) -> float:
        pass

    def evaluate(
        self,
        model: nn.Module,
        data: DataLoader,
        metrics: List[str],
        device: str,
        beta: float,
        optimize: bool = False,
        subset_title: Phase = Phase.TEST,
        group_ids: Optional[List[int]] = None,
        compute_loss: bool = False,
    ) -> DetectionResult:
        model.to(device)
        model.eval()

        probabilities, true_labels = [], []
        total_loss = 0.0
        total_cls_loss = 0.0
        total_contrastive_loss = 0.0
        num_batches = 0
        
        with torch.no_grad():
            for batch in data:
                batch_result = self._evaluation_step(
                    model, batch, device, compute_loss=compute_loss
                )
                
                # Unpack result (backward compatible)
                if len(batch_result) == 4:
                    batch_probs, batch_labels, batch_offsets, batch_loss = batch_result
                    batch_cls_loss = None
                    batch_contrastive_loss = None
                elif len(batch_result) == 6:
                    batch_probs, batch_labels, batch_offsets, batch_loss, batch_cls_loss, batch_contrastive_loss = batch_result
                else:
                    raise ValueError(f'Unexpected _evaluation_step return length: {len(batch_result)}')
                
                if len(batch_offsets.shape) == 2:
                    repeats = batch_offsets[:, 1] - batch_offsets[:, 0]
                    batch_probs = batch_probs.repeat(repeats)
                    batch_labels = batch_labels.repeat(repeats)
                probabilities.extend(batch_probs)
                true_labels.extend(batch_labels)
                
                if compute_loss and batch_loss is not None:
                    total_loss += batch_loss
                    if batch_cls_loss is not None:
                        total_cls_loss += batch_cls_loss
                    if batch_contrastive_loss is not None:
                        total_contrastive_loss += batch_contrastive_loss
                    num_batches += 1

        probabilities = np.array(probabilities)
        true_labels = np.array(true_labels)

        if optimize and self.problem_type == 'binary':
            self.threshold = calibrate_threshold(
                probabilities,
                true_labels,
            )

        if self.problem_type == 'binary':
            predictions = (probabilities > self.threshold).astype(int)
        elif self.problem_type == 'multiclass':
            predictions = np.argmax(probabilities, axis=1)
        else:
            raise ValueError(f'Unknown problem type: {self.problem_type}')

        if self._context_splitter is not None and group_ids is not None:
            predictions, probabilities, true_labels = (
                self._context_splitter.aggregate_predictions(
                    group_ids, predictions, probabilities, true_labels, 
                    binary=(self.problem_type == 'binary')
                )
            )

        if metrics:
            calculated_metrics = calculate_classification_metrics(
                true_labels, probabilities, predictions, metrics, beta
            )
        else:
            calculated_metrics = None

        # Calculate average losses if computed
        avg_loss = None
        avg_cls_loss = None
        avg_contrastive_loss = None
        
        if compute_loss and num_batches > 0:
            avg_loss = total_loss / num_batches
            if total_cls_loss > 0:
                avg_cls_loss = total_cls_loss / num_batches
            if total_contrastive_loss > 0:
                avg_contrastive_loss = total_contrastive_loss / num_batches

        return DetectionResult(
            metrics=calculated_metrics,
            probs=probabilities.tolist(),
            threshold=self.threshold,
        )

    @abstractmethod
    def _evaluation_step(
        self, model: nn.Module, batch: Dict[str, torch.Tensor], device: str, compute_loss: bool = False
    ) -> tuple:
        pass

    def _prepare_batch(
        self, batch: Dict[str, torch.Tensor], device: str
    ) -> Tuple[
        List[torch.Tensor], torch.Tensor, Optional[torch.Tensor], List[torch.Tensor]
    ]:
        hiddens = [batch[col].to(device) for col in batch.keys() if 'hidden' in col]
        labels = batch[TARGET_COL].to(device)
        offsets = None
        if OFFSETS_COL in batch.keys():
            offsets = batch[OFFSETS_COL].to(device)
        att_masks = [
            batch[col].to(device) for col in batch.keys() if 'attention_masks' in col
        ]
        return hiddens, labels, offsets, att_masks

    def _calculate_contrastive_loss(
        self,
        model: nn.Module,
        hiddens: List[torch.Tensor],
        labels: torch.Tensor,
        attention_masks_list: List[torch.Tensor],
    ) -> torch.Tensor:
        """Calculate contrastive loss if the model supports it."""
        if not self.use_contrastive or self.contrastive_loss_fn is None:
            return torch.tensor(0.0, device=labels.device)

        if hasattr(model, 'get_contrastive_projection'):
            projections = model.get_contrastive_projection(
                hiddens, attention_masks_list
            )
            return self.contrastive_loss_fn(projections, labels)
        elif hasattr(model, 'forward_with_projection'):
            projections, _ = model.forward_with_projection(
                hiddens, attention_masks_list
            )
            return self.contrastive_loss_fn(projections, labels)
        else:
            lg.warning(
                "Model doesn't support contrastive learning. Contrastive loss will be ignored."
            )
            return torch.tensor(0.0, device=labels.device)
    
    def _compute_and_log_contrastive_metrics(
        self,
        model: nn.Module,
        data: DataLoader,
        device: str,
        epoch: int,
        max_batches: int = 10,
    ) -> Optional[Dict[str, float]]:
        """
        Computes and logs contrastive learning metrics.
        
        Args:
            model: Model to evaluate
            data: DataLoader with training data
            device: Device to use
            epoch: Current epoch number
            max_batches: Maximum number of batches to use for metrics computation
        
        Returns:
            Dictionary with contrastive metrics or None
        """
        if not self.use_contrastive:
            return None
            
        model.eval()
        all_projections = []
        all_labels = []
        
        with torch.no_grad():
            for batch_idx, batch in enumerate(data):
                if batch_idx >= max_batches:
                    break
                    
                hiddens, labels, _, att_masks = self._prepare_batch(batch, device)
                
                # Get projections
                if hasattr(model, 'get_contrastive_projection'):
                    projections = model.get_contrastive_projection(
                        hiddens, att_masks
                    )
                elif hasattr(model, 'forward_with_projection'):
                    projections, _ = model.forward_with_projection(
                        hiddens, att_masks
                    )
                else:
                    return None
                
                all_projections.append(projections)
                all_labels.append(labels)
        
        model.train()
        
        if not all_projections:
            return None
        
        # Concatenate all batches
        all_projections = torch.cat(all_projections, dim=0)
        all_labels = torch.cat(all_labels, dim=0)
        
        # Compute contrastive metrics
        contrastive_metrics = metrics.compute_contrastive_metrics(
            all_projections, all_labels
        )
        
        # Compute hard negative statistics
        hard_neg_stats = metrics.compute_hard_negative_stats(
            all_projections, all_labels
        )
        
        # Combine metrics
        combined_metrics = {**contrastive_metrics, **hard_neg_stats}
        
        # Log to console
        lg.info(f'Epoch {epoch + 1} Contrastive Metrics:')
        for key, value in combined_metrics.items():
            lg.info(f'  {key}: {value:.4f}')
        
        return combined_metrics


class BinaryHiddenStatesClassifierTrainer(HiddenStatesClassifierTrainerBase):
    def __init__(self, context_splitter: Optional[SplitManager] = None):
        super().__init__(context_splitter=context_splitter)
        self.problem_type = 'binary'

    def _setup_optimizer(self, cfg: TrainingArgsConfig, model: nn.Module):
        self.optimizer = Adam(
            model.parameters(),
            lr=cfg.learning_rate,
            weight_decay=cfg.weight_decay,
        )

    def _setup_scheduler(self, cfg: TrainingArgsConfig, model: nn.Module):
        if hasattr(cfg, 'use_lr_scheduler') and cfg.use_lr_scheduler:
            if self.use_contrastive:
                self.scheduler = ReduceLROnPlateau(
                    self.optimizer, mode='min', factor=0.5, patience=5,
                )
            else:
                self.scheduler = CyclicLR(
                    self.optimizer,
                    base_lr=cfg.learning_rate,
                    max_lr=cfg.max_learning_rate,
                )

    def _setup_additional_loss_fn(self, cfg: TrainingArgsConfig):
        if cfg.loss_function == 'bf1':
            self.loss_fn = metrics.BalancedFScore(beta=cfg.beta, weight=cfg.weight)
        elif cfg.loss_function == 'ff1':
            self.loss_fn = metrics.FuzzyF1(smooth=1e-6)
        elif cfg.loss_function == 'precision':
            self.loss_fn = metrics.SoftPrecisionLoss(smooth=1e-6)
        else:
            self.loss_fn = F.binary_cross_entropy_with_logits

    def _setup_alpha_scheduler(self, cfg):
        if hasattr(cfg, 'use_lr_scheduler') and cfg.use_lr_scheduler:
            if cfg.alpha_scheduler == 'exp':
                self.alpha_scheduler = schedulers.ExponentialAlphaScheduler(
                    alpha=cfg.alpha_start,
                    gamma=cfg.alpha_gamma,
                )
            elif cfg.alpha_scheduler == 'cos':
                self.alpha_scheduler = schedulers.CosineAnnealingScheduler(T_max=5)

    def train_epoch(
        self, model: nn.Module, train_data: DataLoader, device: str
    ):
        """Train for one epoch. Returns dict with loss components."""
        epoch_loss = 0.0
        epoch_cls_loss = 0.0
        epoch_contrastive_loss = 0.0
        
        for batch in tqdm(train_data, desc='Training Epoch'):

            def closure():
                nonlocal epoch_cls_loss, epoch_contrastive_loss
                
                hiddens, labels, _, att_masks = self._prepare_batch(batch, device)
                self.optimizer.zero_grad()

                if self.use_contrastive and hasattr(model, 'forward_with_projection'):
                    projections, outputs = model.forward_with_projection(
                        hiddens, attention_masks_list=att_masks
                    )
                else:
                    outputs = model(hiddens, attention_masks_list=att_masks)
                    projections = None

                if self.zero_bce:
                    loss_cls = torch.tensor(0.0, device=device)
                else:
                    # Handle both single output and two outputs for binary classification
                    if outputs.shape[-1] == 1:
                        # Single output: use binary cross entropy with logits
                        loss_cls = F.binary_cross_entropy_with_logits(
                            outputs.squeeze(-1), labels.float()
                        )
                    elif outputs.shape[-1] == 2:
                        # Two outputs: use cross entropy
                        loss_cls = F.cross_entropy(outputs, labels.long())
                    else:
                        raise ValueError(f'Binary trainer expects 1 or 2 outputs, got {outputs.shape[-1]}')

                # Track classification loss
                epoch_cls_loss += loss_cls.item()
                
                if self.use_contrastive:
                    if projections is not None:
                        loss_contrastive = self.contrastive_loss_fn(projections, labels)
                    else:
                        loss_contrastive = self._calculate_contrastive_loss(
                            model, hiddens, labels, att_masks
                        )
                    
                    # Track contrastive loss (unweighted, consistent with eval)
                    epoch_contrastive_loss += loss_contrastive.item()

                    if self.zero_bce:
                        loss = loss_contrastive
                    else:
                        loss = loss_cls + self.contrastive_weight * loss_contrastive
                else:
                    loss = loss_cls

                if self.alpha_scheduler is not None:
                    # Calculate loss_fn with proper shape handling
                    if outputs.shape[-1] == 1:
                        alt_loss = self.loss_fn(outputs.squeeze(-1), labels.float())
                    elif outputs.shape[-1] == 2:
                        # For 2 outputs, most custom loss functions won't work, use cross entropy
                        alt_loss = F.cross_entropy(outputs, labels.long())
                    else:
                        raise ValueError(f'Binary trainer expects 1 or 2 outputs, got {outputs.shape[-1]}')
                    
                    loss = self.alpha_scheduler.get_lr() * loss_cls + (
                        1 - self.alpha_scheduler.get_lr()
                    ) * alt_loss

                # L2 regularization
                l2 = 0.0
                for name, param in model.named_parameters():
                    if 'bias' not in name:
                        l2 += torch.sum(param**2)
                loss += 0.5 * l2 / hiddens[0].size(0)

                loss.backward()
                if self.use_contrastive:
                    torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                return loss

            loss = self.optimizer.step(closure)
            epoch_loss += loss.item()

        # Return dict with loss components
        result = {
            'total_loss': epoch_loss / len(train_data),
        }
        
        if self.use_contrastive:
            result['cls_loss'] = epoch_cls_loss / len(train_data)
            result['contrastive_loss'] = epoch_contrastive_loss / len(train_data)
        
        return result

    def _evaluation_step(
        self, model: nn.Module, batch: Dict[str, torch.Tensor], device: str, compute_loss: bool = False
    ) -> tuple:
        hiddens, labels, offsets, att_masks = self._prepare_batch(batch, device)

        # Forward pass with projections if using contrastive learning
        projections = None
        if self.use_contrastive and hasattr(model, 'forward_with_projection'):
            projections, outputs = model.forward_with_projection(
                hiddens, attention_masks_list=att_masks
            )
        else:
            outputs = model(hiddens, attention_masks_list=att_masks)

        # Calculate loss if requested
        batch_loss = None
        batch_cls_loss = None
        batch_contrastive_loss = None
        
        if compute_loss:
            # Classification loss (with zero_bce support)
            if self.zero_bce:
                loss_cls = torch.tensor(0.0, device=hiddens[0].device)
            else:
                if outputs.shape[-1] == 1:
                    # Single output: binary cross entropy with logits
                    loss_cls = F.binary_cross_entropy_with_logits(
                        outputs.squeeze(-1), labels.float()
                    )
                elif outputs.shape[-1] == 2:
                    # Two outputs: cross entropy
                    loss_cls = F.cross_entropy(outputs, labels.long())
                else:
                    raise ValueError(f'Binary trainer expects 1 or 2 outputs, got {outputs.shape[-1]}')
            
            batch_cls_loss = loss_cls.item()
            
            # Add contrastive loss if enabled
            if self.use_contrastive:
                if projections is not None:
                    loss_contrastive = self.contrastive_loss_fn(projections, labels)
                else:
                    loss_contrastive = self._calculate_contrastive_loss(
                        model, hiddens, labels, att_masks
                    )
                # Store unweighted contrastive loss (consistent with train_epoch)
                batch_contrastive_loss = loss_contrastive.item()
                
                # Combine losses (with zero_bce support)
                if self.zero_bce:
                    total_loss = loss_contrastive
                else:
                    total_loss = loss_cls + self.contrastive_weight * loss_contrastive
            else:
                total_loss = loss_cls
            
            # Add L2 regularization (consistent with train_epoch)
            l2 = 0.0
            for name, param in model.named_parameters():
                if 'bias' not in name:
                    l2 += torch.sum(param**2)
            total_loss = total_loss + 0.5 * l2 / hiddens[0].size(0)
            
            batch_loss = total_loss.item()

        # Handle both single output and two outputs for binary classification
        if outputs.shape[-1] == 1:
            # Single output: use sigmoid
            probs = torch.sigmoid(outputs).squeeze(-1).cpu().numpy()
        elif outputs.shape[-1] == 2:
            # Two outputs: use softmax and take probability of class 1
            probs = torch.softmax(outputs, dim=-1)[:, 1].cpu().numpy()
        else:
            raise ValueError(f'Binary trainer expects 1 or 2 outputs, got {outputs.shape[-1]}')
            
        if offsets is not None:
            offsets = offsets.cpu().numpy()
        return probs, labels.cpu().numpy(), offsets, batch_loss, batch_cls_loss, batch_contrastive_loss


class MultiClassHiddenStatesClassifierTrainer(HiddenStatesClassifierTrainerBase):
    def __init__(self, context_splitter: Optional[SplitManager] = None):
        super().__init__(context_splitter=context_splitter)
        self.problem_type = 'multiclass'

    def _setup_optimizer(self, cfg: TrainingArgsConfig, model: nn.Module):
        self.optimizer = Adam(
            model.parameters(),
            lr=cfg.learning_rate,
            weight_decay=cfg.weight_decay,
        )

    def _setup_scheduler(self, cfg: TrainingArgsConfig, model: nn.Module):
        if (
            self.use_contrastive
            and hasattr(cfg, 'use_lr_scheduler')
            and cfg.use_lr_scheduler
        ):
            self.scheduler = ReduceLROnPlateau(
                self.optimizer, mode='min', factor=0.5, patience=5
            )
        else:
            self.scheduler = CyclicLR(
                self.optimizer,
                base_lr=cfg.learning_rate,
                max_lr=cfg.max_learning_rate,
            )

    def _setup_additional_loss_fn(self, cfg: TrainingArgsConfig):
        if cfg.loss_function == 'cross_entropy':
            self.loss_fn = nn.CrossEntropyLoss()
        elif cfg.loss_function == 'label_smoothing':
            self.loss_fn = nn.CrossEntropyLoss(
                label_smoothing=cfg.label_smoothing
                if hasattr(cfg, 'label_smoothing')
                else 0.1
            )
        else:
            self.loss_fn = nn.CrossEntropyLoss()

    def _setup_alpha_scheduler(self, cfg):
        if hasattr(cfg, 'use_lr_scheduler') and cfg.use_lr_scheduler:
            if cfg.alpha_scheduler == 'exp':
                self.alpha_scheduler = schedulers.ExponentialAlphaScheduler(
                    alpha=cfg.alpha_start,
                    gamma=cfg.alpha_gamma,
                )
            elif cfg.alpha_scheduler == 'cos':
                self.alpha_scheduler = schedulers.CosineAnnealingScheduler(T_max=5)

    def train_epoch(
        self, model: nn.Module, train_data: DataLoader, device: str
    ):
        """Train for one epoch. Returns dict with loss components."""
        epoch_loss = 0.0
        epoch_cls_loss = 0.0
        epoch_contrastive_loss = 0.0
        
        for batch in tqdm(train_data, desc='Training Epoch'):

            def closure():
                nonlocal epoch_cls_loss, epoch_contrastive_loss
                
                hiddens, labels, _, att_masks = self._prepare_batch(batch, device)
                self.optimizer.zero_grad()

                if self.use_contrastive and hasattr(model, 'forward_with_projection'):
                    projections, outputs = model.forward_with_projection(
                        hiddens, attention_masks_list=att_masks
                    )
                else:
                    outputs = model(hiddens, attention_masks_list=att_masks)
                    projections = None

                if outputs.dim() > 2:
                    outputs = outputs.view(outputs.size(0), -1)
                if labels.dim() > 1:
                    labels = labels.squeeze(-1)

                loss_cls = self.loss_fn(outputs, labels.long())
                
                # Track classification loss
                epoch_cls_loss += loss_cls.item()

                if self.use_contrastive:
                    if projections is not None:
                        loss_contrastive = self.contrastive_loss_fn(projections, labels)
                    else:
                        loss_contrastive = self._calculate_contrastive_loss(
                            model, hiddens, labels, att_masks
                        )
                    
                    # Track contrastive loss
                    epoch_contrastive_loss += loss_contrastive.item()

                    loss = loss_cls + self.contrastive_weight * loss_contrastive
                else:
                    loss = loss_cls

                # L2 regularization
                l2 = 0.0
                for name, param in model.named_parameters():
                    if 'bias' not in name:
                        l2 += torch.sum(param**2)
                loss += 0.5 * l2 / hiddens[0].size(0)

                loss.backward()
                if self.use_contrastive:
                    torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                return loss

            loss = self.optimizer.step(closure)
            epoch_loss += loss.item()

        # Return dict with loss components
        result = {
            'total_loss': epoch_loss / len(train_data),
        }
        
        if self.use_contrastive:
            result['cls_loss'] = epoch_cls_loss / len(train_data)
            result['contrastive_loss'] = epoch_contrastive_loss / len(train_data)
        
        return result

    def _evaluation_step(
        self, model: nn.Module, batch: Dict[str, torch.Tensor], device: str, compute_loss: bool = False
    ) -> tuple:
        hiddens, labels, _, att_masks = self._prepare_batch(batch, device)

        # Forward pass with projections if using contrastive learning
        projections = None
        if hasattr(model, 'forward_with_projection'):
            projections, outputs = model.forward_with_projection(
                hiddens, attention_masks_list=att_masks
            )
        else:
            outputs = model(hiddens, attention_masks_list=att_masks)

        # Calculate loss if requested
        batch_loss = None
        batch_cls_loss = None
        batch_contrastive_loss = None
        
        if compute_loss:
            # Prepare outputs and labels for loss calculation
            if outputs.dim() > 2:
                outputs_for_loss = outputs.view(outputs.size(0), -1)
            else:
                outputs_for_loss = outputs
            if labels.dim() > 1:
                labels_for_loss = labels.squeeze(-1)
            else:
                labels_for_loss = labels
            
            # Classification loss
            loss_cls = self.loss_fn(outputs_for_loss, labels_for_loss.long())
            batch_cls_loss = loss_cls.item()
            
            # Add contrastive loss if enabled
            if self.use_contrastive:
                if projections is not None:
                    loss_contrastive = self.contrastive_loss_fn(projections, labels)
                else:
                    loss_contrastive = self._calculate_contrastive_loss(
                        model, hiddens, labels, att_masks
                    )
                # Store unweighted contrastive loss (consistent with train_epoch)
                batch_contrastive_loss = loss_contrastive.item()
                total_loss = loss_cls + self.contrastive_weight * loss_contrastive
            else:
                total_loss = loss_cls
            
            # Add L2 regularization (consistent with train_epoch)
            l2 = 0.0
            for name, param in model.named_parameters():
                if 'bias' not in name:
                    l2 += torch.sum(param**2)
            total_loss = total_loss + 0.5 * l2 / hiddens[0].size(0)
            
            batch_loss = total_loss.item()

        probs = F.softmax(outputs, dim=-1).cpu().numpy()
        return probs, labels.cpu().numpy(), torch.zeros_like(labels).cpu().numpy(), batch_loss, batch_cls_loss, batch_contrastive_loss
