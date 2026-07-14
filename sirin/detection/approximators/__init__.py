from .base import TargetApproximatorBase

__all__ = ["TargetApproximatorBase", "SEPTargetApproximator"]


def __getattr__(name):
    if name != "SEPTargetApproximator":
        raise AttributeError(name)

    try:
        from .sep import SEPTargetApproximator
    except ModuleNotFoundError as exc:
        if exc.name == "lm_polygraph":
            raise ModuleNotFoundError(
                "SEPTargetApproximator requires the optional lm_polygraph dependency"
            ) from exc
        raise
    return SEPTargetApproximator
