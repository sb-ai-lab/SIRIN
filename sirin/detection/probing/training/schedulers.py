import math


class CosineAnnealingScheduler:
    def __init__(
        self,
        T_max: int,
        base_lr: float = 1.0,
        eta_min: float = 0.0,
        last_epoch: int = -1,
    ):
        self.T_max = T_max
        self.eta_min = eta_min
        self.alpha = base_lr
        self.base_lr = base_lr
        self.last_epoch = last_epoch
        self.steps = 0

    def step(self):
        self.steps += 1
        self.last_epoch += 1

    def get_lr(self):
        if self.last_epoch == 0:
            return self.alpha
        elif self.steps == 1 and self.last_epoch > 0:
            return (
                self.eta_min
                + (self.base_lr - self.eta_min)
                * (1 + math.cos((self.last_epoch) * math.pi / self.T_max))
                / 2
            )
        elif (self.last_epoch - 1 - self.T_max) % (2 * self.T_max) == 0:
            return (
                self.alpha
                + (self.base_lr - self.eta_min)
                * (1 - math.cos(math.pi / self.T_max))
                / 2
            )
        return (1 + math.cos(math.pi * self.last_epoch / self.T_max)) / (
            1 + math.cos(math.pi * (self.last_epoch - 1) / self.T_max)
        ) * (self.alpha - self.eta_min) + self.eta_min


class ExponentialAlphaScheduler:
    def __init__(self, alpha: int = 1, gamma: int = 0.95):
        self.alpha = alpha
        self.gamma = gamma

    def step(self):
        self.alpha *= self.gamma

    def get_lr(self):
        return self.alpha