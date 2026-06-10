from enum import Enum
from typing import Union

import torch
from omegaconf import DictConfig, ListConfig

CfgDictType = Union[dict, DictConfig]
CfgListType = Union[list, ListConfig]


class TorchDtype(Enum):
    bf16 = torch.bfloat16
    f64 = torch.float64
    f32 = torch.float32
    f16 = torch.float16
    c32 = torch.complex32
    c64 = torch.complex64
    c128 = torch.complex128
    i8 = torch.int8
    i16 = torch.int16
    i32 = torch.int32
    i64 = torch.int64
    b8 = torch.bool
    u8 = torch.uint8

    @staticmethod
    def from_str(dtype_name: str) -> torch.dtype:
        return TorchDtype[dtype_name].value

    @staticmethod
    def from_dtype(dtype: torch.dtype) -> str:
        for dtype_member in TorchDtype:
            if dtype_member.value == dtype:
                return dtype_member.name
        raise ValueError(f"Unknown dtype: {dtype}.")
