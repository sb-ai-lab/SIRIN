from dotenv import load_dotenv
from typing import Any

import hydra
from omegaconf import DictConfig
from sirin.utils.config_manager import ConfigManager

load_dotenv()

@hydra.main(version_base=None, config_path="../sirin/configs", config_name="train")
def main(cfg: DictConfig) -> Any:
    config_manager = ConfigManager(cfg)
    pipeline = config_manager.build_pipeline()
    pipeline.train()


if __name__ == "__main__":
    main()
