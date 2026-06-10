from typing import Any, Optional, Union

import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import Trainer


class SequenceDecoderJudgeTrainer(Trainer):
    def __init__(self, class_token_ids, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.processing_class = kwargs['processing_class']
        self.counter = 0
        self.class_token_ids = class_token_ids

    def prediction_step(
        self,
        model: nn.Module,
        inputs: dict[str, Union[torch.Tensor, Any]],
        prediction_loss_only: bool,
        ignore_keys: Optional[list[str]] = None,
    ) -> tuple[Optional[torch.Tensor], Optional[torch.Tensor], Optional[torch.Tensor]]:
        if model.training:
            return super().prediction_step(
                model, inputs, prediction_loss_only, ignore_keys
            )
        else:
            with torch.no_grad():
                eval_pred = super().prediction_step(
                    model, inputs, prediction_loss_only, ignore_keys
                )
                loss, logits, label_ids = eval_pred

                first_token_idx = (label_ids != -100).float().argmax(dim=1) - 1

                targets = [
                    self.processing_class.decode(label)
                    for label in label_ids[
                        range(len(first_token_idx)), first_token_idx + 1
                    ]
                ]
                targets = torch.tensor(list(map(int, targets)))

                logits = logits[range(len(first_token_idx)), first_token_idx]
                logits = logits[:, self.class_token_ids]
                log_probs = F.softmax(logits, dim=-1)
                if len(self.class_token_ids) == 2:
                    log_probs = log_probs[:, 1]

                return (
                    loss.detach() if loss is not None else None,
                    log_probs.cpu(),
                    targets,
                )
