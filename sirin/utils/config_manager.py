import os
import sys
from functools import wraps
from typing import get_type_hints

import datasets
import hydra
from hydra.core.hydra_config import HydraConfig
from loguru import logger as lg
from omegaconf import DictConfig, OmegaConf

from sirin.definitions import HF_TOKEN_ENV, OPENAI_API_KEY_ENV


class ConfigManager:
    def __init__(self, cfg: DictConfig):
        self.cfg = cfg
        self._setup_environment()
        self._setup_logging(cfg)
        lg.info('Config loaded:')
        lg.info(OmegaConf.to_yaml(cfg))

    def _setup_environment(self):
        os.environ[HF_TOKEN_ENV] = (self.cfg.hf_token or os.environ.get(HF_TOKEN_ENV, ''))
        os.environ[OPENAI_API_KEY_ENV] = (self.cfg.openai_api_key or os.environ.get(OPENAI_API_KEY_ENV, ''))
        os.environ['CUDA_DEVICE_ORDER'] = 'PCI_BUS_ID'
        os.environ['CUDA_VISIBLE_DEVICES'] = self.cfg.cuda_visible_devices

    def _setup_logging(
            self,
            cfg: DictConfig,
        ) -> None:
            lg.configure(
                handlers=[
                    {
                        'sink': sys.stdout,
                        'level': cfg.log_level,
                    }
                ]
            )

            hydra_path = HydraConfig.get().runtime.output_dir
            lg.add(os.path.join(hydra_path, 'main.log'))

    def load_datasets(self):
        if not self.cfg.get('train_dataset_path') or not self.cfg.get(
            'eval_dataset_path'
        ):
            raise ValueError('Please set train_dataset_path and eval_dataset_path')

        train_dataset = datasets.load_from_disk(self.cfg.train_dataset_path)
        eval_dataset = datasets.load_from_disk(self.cfg.eval_dataset_path)
        return train_dataset, eval_dataset

    def build_pipeline(self):
        train_dataset, eval_dataset = self.load_datasets()

        components = {}

        components['extractor_adapter'] = hydra.utils.instantiate(
            self.cfg.model_adapter
        )

        components['feature_processor'] = hydra.utils.instantiate(
            self.cfg.feature_processor,
            extractor=components['extractor_adapter'],
        )

        components['detector'] = hydra.utils.instantiate(
            self.cfg.detector, feature_processor=components['feature_processor']
        )

        components['pipeline'] = hydra.utils.instantiate(
            self.cfg.pipeline,
            detector=components['detector'],
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            generator_adapter=components['extractor_adapter'],
        )

        return components['pipeline']


def validate_hydra_config(func):
    @wraps(func)
    def wrapper(self, config, *args, **kwargs):
        # Get type hints for the function
        type_hints = get_type_hints(func)

        # Get the expected type for the 'config' parameter
        expected_config_type = type_hints.get('config')

        if expected_config_type and isinstance(config, DictConfig):
            config = expected_config_type(**config)

        return func(self, config, *args, **kwargs)

    return wrapper
