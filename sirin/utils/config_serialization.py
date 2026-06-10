"""Utilities for serialization and deserialization of detector and judge configurations."""

from dataclasses import asdict
from typing import Any, Dict, Type, Union

from sirin.models.detection import (
    CompressionConfig,
    HfJudgeConfig,
    JudgeBaseConfig,
    OpenAIJudgeConfig,
    ProbingDetectorConfig,
    SplitConfig,
    UncertaintyDetectorConfig,
)


# ============================================================================
# Probing Detectors Serialization
# ============================================================================


def serialize_probing_detector_config(config: ProbingDetectorConfig, threshold: float) -> Dict[str, Any]:
    """
    Serialize probing detector configuration to dictionary.
    
    Uses asdict from dataclasses for full serialization of all fields,
    including nested configurations and inherited fields from DetectorBaseConfig.
    
    Args:
        config: Probing detector configuration
        threshold: Classification threshold
        
    Returns:
        Dictionary with full configuration
    """
    config_dict = asdict(config)
    config_dict['threshold'] = threshold
    return config_dict


def deserialize_probing_detector_config(config_dict: Dict[str, Any]) -> tuple[ProbingDetectorConfig, float]:
    """
    Deserialize probing detector configuration from dictionary.
    
    Handles nested configurations (CompressionConfig, SplitConfig) and all inherited fields.
    
    Args:
        config_dict: Dictionary with configuration
        
    Returns:
        Tuple (config, threshold)
    """
    # Extract threshold separately
    threshold = config_dict.pop('threshold', 0.5)
    
    # Handle nested configurations
    if 'compression' in config_dict and isinstance(config_dict['compression'], dict):
        config_dict['compression'] = CompressionConfig(**config_dict['compression'])
    
    if 'context_split_config' in config_dict and config_dict['context_split_config'] is not None:
        if isinstance(config_dict['context_split_config'], dict):
            config_dict['context_split_config'] = SplitConfig(**config_dict['context_split_config'])
    
    # Restore full configuration
    config = ProbingDetectorConfig(**config_dict)
    
    return config, threshold


# ============================================================================
# Judges Serialization
# ============================================================================


def serialize_judge_config(
    config: Union[JudgeBaseConfig, HfJudgeConfig, OpenAIJudgeConfig],
    threshold: float,
    model_adapter: Any,
    model_path: str,
) -> Dict[str, Any]:
    """
    Serialize judge configuration to dictionary for saving.
    
    Uses asdict from dataclasses for full serialization of all fields.
    
    Args:
        config: Judge configuration (JudgeBaseConfig, HfJudgeConfig, or OpenAIJudgeConfig)
        threshold: Classification threshold
        model_adapter: Model adapter
        model_path: Path for saving the model
        
    Returns:
        Dictionary with full configuration
    """
    config_dict = asdict(config)
    
    # Add additional parameters
    config_dict['threshold'] = threshold
    config_dict['adapter_config'] = model_adapter
    config_dict['model_path'] = model_path
    
    # Save configuration type for proper deserialization
    config_dict['_config_type'] = type(config).__name__
    
    return config_dict


def deserialize_judge_config(
    config_dict: Dict[str, Any]
) -> tuple[Union[JudgeBaseConfig, HfJudgeConfig, OpenAIJudgeConfig], float, Any, str]:
    """
    Deserialize judge configuration from dictionary after loading.
    
    Restores all configuration fields and additional parameters.
    
    Args:
        config_dict: Dictionary with configuration
        
    Returns:
        Tuple (config, threshold, adapter_config, model_path)
    """
    # Extract additional parameters
    threshold = config_dict.pop('threshold', 0.5)
    adapter_config = config_dict.pop('adapter_config', None)
    model_path = config_dict.pop('model_path', None)
    config_type_name = config_dict.pop('_config_type', 'JudgeBaseConfig')
    
    # Determine configuration type
    config_type_map = {
        'JudgeBaseConfig': JudgeBaseConfig,
        'HfJudgeConfig': HfJudgeConfig,
        'OpenAIJudgeConfig': OpenAIJudgeConfig,
    }
    
    config_type = config_type_map.get(config_type_name, JudgeBaseConfig)
    
    # Handle peft_config (if present) - it should not be serialized as dict
    # because it's a complex object from PEFT library
    if 'peft_config' in config_dict and config_dict['peft_config'] is not None:
        # Leave as is, since peft_config can be a complex object
        pass
    
    # Restore configuration
    config = config_type(**config_dict)
    
    return config, threshold, adapter_config, model_path


# ============================================================================
# Uncertainty Detector Serialization
# ============================================================================


def serialize_uncertainty_detector_config(
    config: UncertaintyDetectorConfig,
    threshold: float,
    feature_stats: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Serialize uncertainty detector configuration to dictionary for saving.
    
    Uses asdict from dataclasses for full serialization of all fields.
    
    Args:
        config: Uncertainty detector configuration
        threshold: Classification threshold
        feature_stats: Feature statistics dictionary
        
    Returns:
        Dictionary with full configuration
    """
    config_dict = asdict(config)
    config_dict['threshold'] = threshold
    config_dict['feature_stats'] = feature_stats
    return config_dict


def deserialize_uncertainty_detector_config(
    config_dict: Dict[str, Any]
) -> tuple[UncertaintyDetectorConfig, float, Dict[str, Any]]:
    """
    Deserialize uncertainty detector configuration from dictionary after loading.
    
    Restores all fields including feature statistics.
    
    Args:
        config_dict: Dictionary with configuration
        
    Returns:
        Tuple (config, threshold, feature_stats)
    """
    # Extract additional parameters separately
    threshold = config_dict.pop('threshold', 0.5)
    feature_stats = config_dict.pop('feature_stats', {})
    
    # Restore full configuration
    config = UncertaintyDetectorConfig(**config_dict)
    
    return config, threshold, feature_stats


