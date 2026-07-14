from copy import deepcopy
from enum import Enum
import importlib
from importlib import import_module
import inspect
import json
from pathlib import Path
import sys
import tempfile
import types

import joblib
import torch
from loguru import logger as lg
from tabpfn import model_loading
import tabpfn.inference as tabpfn_inference
import tabpfn.preprocessing as tabpfn_preprocessing

if not hasattr(tabpfn_inference, 'ClassifierEvalMetrics'):
    class ClassifierEvalMetrics(str, Enum):
        accuracy = 'accuracy'

    tabpfn_inference.ClassifierEvalMetrics = ClassifierEvalMetrics

sys.modules.setdefault('tabpfn.inference_tuning', tabpfn_inference)
sys.modules.setdefault('tabpfn.preprocessing.definitions', tabpfn_preprocessing)

for module_name in (
    'preprocessing_helpers',
    'remove_constant_features_step',
    'reshape_feature_distribution_step',
    'encode_categorical_features_step',
    'add_fingerprint_features_step',
    'shuffle_features_step',
):
    target = f"tabpfn.preprocessing.steps.{module_name}"
    try:
        importlib.import_module(target)
        continue  # newer tabpfn (>= 6) ships this path natively — nothing to alias.
    except ModuleNotFoundError:
        pass
    sys.modules.setdefault(
        target,
        importlib.import_module(f"tabpfn.preprocessors.{module_name}"),
    )

_SQUASHING_MODULE = 'tabpfn.preprocessing.steps.squashing_scaler_transformer'
try:
    import_module(_SQUASHING_MODULE)
except ModuleNotFoundError as exc:
    if exc.name is None or not (
        exc.name == _SQUASHING_MODULE or _SQUASHING_MODULE.startswith(exc.name + '.')
    ):
        raise
    squashing_mod = types.ModuleType(_SQUASHING_MODULE)

    class SquashingScaler:
        def __init__(
            self,
            max_absolute_value: float = 3.0,
            quantile_range: tuple[float, float] = (25.0, 75.0),
        ):
            self.max_absolute_value = max_absolute_value
            self.quantile_range = quantile_range

        def fit(self, X, y=None):
            return self

        def transform(self, X):
            raise RuntimeError(
                "tabpfn SquashingScaler is unavailable in this tabpfn build, so its "
                "transform cannot be reproduced faithfully. Refusing to silently substitute "
                "a clip-only approximation (predictions would differ) — retrain the TabPFN "
                "detector, or install a tabpfn version that ships SquashingScaler."
            )

        def fit_transform(self, X, y=None):
            return self.transform(X)

    squashing_mod.SquashingScaler = SquashingScaler
    sys.modules[_SQUASHING_MODULE] = squashing_mod

if 'tabpfn.inference_config' not in sys.modules:
    inference_config_mod = types.ModuleType('tabpfn.inference_config')

    class InferenceConfig:
        pass

    inference_config_mod.InferenceConfig = InferenceConfig
    sys.modules['tabpfn.inference_config'] = inference_config_mod


def _filter_tabpfn_init_params(cls, params: dict) -> dict:
    allowed = set(inspect.signature(cls).parameters)
    dropped = sorted(set(params) - allowed)
    if dropped:
        lg.warning(f"Dropping legacy TabPFN init params for {cls.__name__}: {dropped}")
    return {key: value for key, value in params.items() if key in allowed}


def load_fitted_tabpfn_model_compat(path: Path | str, *, device: str | torch.device = 'cpu'):
    path = Path(path)
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        model_loading._extract_archive(path, tmp)

        with (tmp / 'init_params.json').open() as f:
            params = json.load(f)

        saved_cls_name = params.pop('__class_name__')
        if isinstance(params.get('inference_precision'), str) and params[
            'inference_precision'
        ].startswith('torch.'):
            dtype_name = params['inference_precision'].split('.')[1]
            params['inference_precision'] = getattr(torch, dtype_name)
        params['device'] = device

        if saved_cls_name == 'TabPFNClassifier':
            cls = import_module('tabpfn.classifier').TabPFNClassifier
        elif saved_cls_name == 'TabPFNRegressor':
            cls = import_module('tabpfn.regressor').TabPFNRegressor
        else:
            raise TypeError(f"Unknown estimator class '{saved_cls_name}'")

        est = cls(**_filter_tabpfn_init_params(cls, params))
        est._initialize_model_variables()

        fitted_attrs = joblib.load(tmp / 'fitted_attrs.joblib')
        for key, value in fitted_attrs.items():
            setattr(est, key, value)

        est.executor_ = model_loading.InferenceEngine.load_state(
            tmp / 'executor_state.joblib'
        )

        if not hasattr(est.executor_, 'model') or est.executor_.model is None:
            est.executor_.model = est.model_

        if not hasattr(est.executor_, 'models') or est.executor_.models is None:
            est.executor_.models = [
                deepcopy(est.model_) for _ in range(len(est.executor_.ensemble_configs))
            ]

        est.devices_ = (torch.device(device),)
        if hasattr(est.executor_, 'model') and est.executor_.model is not None:
            est.executor_.model.to(device)
        if hasattr(est.executor_, 'models'):
            est.executor_.models = [model.to(device) for model in est.executor_.models]

        for key, value in vars(est).items():
            if key.endswith('_') and hasattr(value, 'to'):
                setattr(est, key, value.to(device))

        return est
