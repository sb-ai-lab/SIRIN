from typing import Tuple, Type, Union
from loguru import logger as lg

from hydra._internal.instantiate._instantiate2 import _resolve_target


def check_hydra_target_issubclass(
    class_name: str,
    instance_of: Union[Type, Tuple[Type, ...]],
    check_if_meta: bool = False,
) -> bool:
    target = _resolve_target(class_name, '')
    check_result = issubclass(target, instance_of)

    if check_if_meta:
        msg_type = "metaclass"
    else:
        msg_type = "subclass"

    if not check_result:
        raise TypeError(
            f"The class `{class_name}` is not a {msg_type} of `{instance_of.__name__}`."
        )

    return check_result


def check_nonexisting_args(
    kwargs: dict,
    raise_excepion: bool = False,
    raise_warning: bool = True,
) -> None:
    """
    Helper function in case when arguments are passed as dictionary
    and we want to check if there are any unknown arguments.
    """
    if kwargs:
        if raise_excepion:
            raise TypeError(f"Unknown arguments: {kwargs.keys()}")
        elif raise_warning:
            lg.warning(f"Unknown arguments: {kwargs.keys()}")
