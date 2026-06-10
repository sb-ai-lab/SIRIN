import os
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import joblib
import yaml
from datasets import Dataset
from joblib import Parallel, delayed
from loguru import logger as lg
from tqdm import tqdm

from sirin.definitions import (
    ARTIFACTS_YAML,
    HIDDENS_FILE_KEY,
    METRICS_KEY,
    TORCH_MODULE_KEY,
)


class BaseAliasSaver:
    def __init__(
        self,
        name: str,
        save_dir: str,
        file_type_alias: str,
        save_fn: Callable[..., Any],
        suffix: Optional[str] = None,
        create_dir: bool = True,
    ):
        self.name = name
        self.save_dir = save_dir
        self.file_type_alias = file_type_alias
        self.save_fn = save_fn
        self.suffix = suffix or ''
        self.create_dir = create_dir
        self.save_path = self.get_save_path(save_dir, name, suffix)

    def get_save_path(self, save_dir: str, name: str, suffix: Optional[str] = None) -> Path:
        """Generate the base save path from components."""
        full_suffix = '/'.join([self.file_type_alias, name, suffix or '']).strip('/')
        save_path = Path(save_dir) / full_suffix
        if self.create_dir:
            os.makedirs(save_path.parent, exist_ok=True)
        return save_path

    def save(self, *save_args, label: Optional[str] = None, **save_kwgs):
        """Save data with optional label suffix and register the artifact."""

        if label:
            curr_save_path = self._get_labeled_path(label)
            artifact_key = f"{self.file_type_alias}_{label}"
        else:
            curr_save_path = self.save_path
            artifact_key = self.file_type_alias

        lg.info(f"Saving at {curr_save_path}.")
        self.save_fn(curr_save_path, *save_args, **save_kwgs)

        with open(Path(self.save_dir) / ARTIFACTS_YAML, "a") as f:
            yaml.dump({artifact_key: str(curr_save_path.resolve())}, f)

    def _get_labeled_path(self, label: str) -> Path:
        """Create a path with a label added."""
        splitted_path = str(self.save_path).split(".")
        labled_path = ".".join([f"{splitted_path[0]}_{label}"] + splitted_path[1:])
        return Path(labled_path)


class DatasetSaver(BaseAliasSaver):
    def __init__(
        self,
        name: str,
        save_dir: str,
        file_type_alias: str,
        create_dir: bool = True,
    ):
        super().__init__(
            name=name,
            save_dir=save_dir,
            file_type_alias=file_type_alias,
            save_fn=self._save_logic,
            create_dir=create_dir,
        )

    def _save_logic(
        self,
        save_path: Path,
        dataset: Dataset,
        description: Optional[str] = None,
    ):
        dataset.info.description = description
        dataset.save_to_disk(str(save_path))


class BatchCheckpointSaver(BaseAliasSaver):
    def __init__(
        self,
        data_name: str,
        model_name: str,
        save_dir: str,
        suffix: str = ".pkl",
        file_type_alias: str = HIDDENS_FILE_KEY,
        create_dir: bool = True,
    ):
        super().__init__(
            name="_".join([data_name, model_name]),
            save_dir=save_dir,
            file_type_alias=file_type_alias,
            save_fn=self._save_logic,
            suffix=suffix,
            create_dir=create_dir,
        )

    def _save_logic(self, savepath: Path, **kwargs):
        joblib.dump(kwargs, savepath)

    def save_checkpoint(self, start_idx: int, end_idx: int, **kwargs):
        checkpoint_path = (
            Path(self.save_dir) / f"checkpoint_{start_idx}_{end_idx}{self.suffix}"
        )
        lg.info(f"Saving checkpoint: {checkpoint_path}")
        joblib.dump(kwargs, checkpoint_path)

    def load_single_checkpoint(self, checkpoint_file: Path) -> Dict[str, Any]:
        return joblib.load(checkpoint_file)

    def load_checkpoints(
        self, checkpoint_sources: List[str], n_jobs: int = -1, use_tqdm: bool = True
    ) -> Dict[str, List]:
        checkpoint_files = sorted(
            map(Path, checkpoint_sources),
            key=lambda x: self._get_checkpoint_indices(x)[0],
        )

        if use_tqdm:
            iterator = tqdm(checkpoint_files, desc="Loading checkpoints")
        else:
            iterator = checkpoint_files

        results = Parallel(n_jobs=n_jobs)(
            delayed(self.load_single_checkpoint)(cf) for cf in iterator
        )

        aggregated_data = {}
        for result in results:
            for key, value in result.items():
                if key not in aggregated_data:
                    aggregated_data[key] = []
                aggregated_data[key].extend(value)

        return aggregated_data

    def _get_checkpoint_indices(self, filename: Path) -> Tuple[int, int]:
        pattern = r"checkpoint_(\d+)_(\d+)"
        match = re.match(pattern, filename.stem)
        assert match, f"Incorrect checkpoint filename `{filename}`."
        start_idx, end_idx = map(int, match.groups())
        return start_idx, end_idx

    def get_processed_indices(self, checkpoint_dir: Path) -> Set[int]:
        checkpoint_files = checkpoint_dir.glob(f"checkpoint_*{self.suffix}")
        processed_indices = set()
        for checkpoint_file in checkpoint_files:
            start_idx, end_idx = self._get_checkpoint_indices(checkpoint_file)
            processed_indices.update(range(start_idx, end_idx + 1))
        return processed_indices


class TorchModulelSaver(BaseAliasSaver):
    import torch

    def __init__(
        self,
        name: str,
        save_dir: str,
        create_dir: bool = True,
    ):
        super().__init__(
            name=name,
            save_dir=save_dir,
            file_type_alias=TORCH_MODULE_KEY,
            save_fn=self._save_logic,
            suffix=".pt",
            create_dir=create_dir,
        )

    def _save_logic(
        self,
        save_path: Path,
        module: torch.nn.Module,
    ):
        import torch

        torch.save(module.state_dict(), str(save_path))
        lg.info(f"Module is saved to {save_path}")

    def save_checkpoint(
        self,
        checkpoint_name: str,
        module: torch.nn.Module,
    ) -> Path:
        import torch

        checkpoint_path = self.get_save_path(self.save_dir, checkpoint_name, ".pt")
        lg.info(f"Saving module checkpoint to {checkpoint_path}")
        torch.save(module.state_dict(), checkpoint_path)
        return checkpoint_path


class MetricsSaver(BatchCheckpointSaver):
    def __init__(
        self,
        data_name: str,
        model_name: str,
        save_dir: str,
        create_dir: bool = True,
    ):
        super().__init__(
            name="_".join([data_name, model_name]),
            save_dir=save_dir,
            file_type_alias=METRICS_KEY,
            save_fn=self._save_logic,
            suffix="_metrics.pkl",
            create_dir=create_dir,
        )
