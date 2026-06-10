from typing import Any, Dict, Sequence, Optional

import datasets


def add_or_replace_column(
    dataset: datasets.Dataset, column: str, new_values: Any
) -> datasets.Dataset:
    if column in dataset.column_names:

        def replace_column(item: Dict, idx: int) -> Dict:
            item[column] = new_values[idx]
            return item

        dataset = dataset.map(replace_column, with_indices=True)
    else:
        dataset = dataset.add_column(column, new_values)
    return dataset


def filter_columns(
    dataset: datasets.Dataset,
    columns: Sequence[str],
) -> datasets.Dataset:
    columns_to_save = [col for col in columns if col in dataset.column_names]
    return dataset.select_columns(columns_to_save)


def safe_filter_columns(
    dataset: datasets.Dataset,
    columns_to_save: Sequence[str],
) -> datasets.Dataset:
    columns_to_save = set(columns_to_save)
    dataset_columns = set(dataset.column_names)
    columns_to_drop = dataset_columns - columns_to_save
    if columns_to_drop:
        dataset = dataset.remove_columns(columns_to_drop)

    missing_columns = columns_to_save - dataset_columns
    if missing_columns:
        for column in missing_columns:
            dataset = dataset.add_column(column, [None] * len(dataset))

    return dataset


def get_assistant_prefix(model_name: str) -> str:
    model_patterns = {
        "qwen": "<|im_start|>assistant\n",
        "llama": "ASSISTANT:",
        "mistral": "[INST]",
        "chatml": "<|im_start|>assistant\n",
        "zephyr": "<|assistant|>",
    }

    # Check model name for known patterns
    for key, prefix in model_patterns.items():
        if key in model_name.lower():
            return prefix

    # Default fallback
    return "<|im_start|>assistant\n"


def get_dataset_identifier(dataset: datasets.Dataset|datasets.DatasetDict) -> str:

    def extract_identifier(info: datasets.DatasetInfo) -> Optional[str]:
        if info.dataset_name:
            return info.dataset_name
        elif info.builder_name:
            return info.builder_name
        elif info.config_name:
            return f'config_{info.config_name}'
        else:
            return None
    
    identifier = None
    if isinstance(dataset, datasets.DatasetDict):
        first_split = next(iter(dataset.keys()))
        identifier = extract_identifier(dataset[first_split].info)
    elif isinstance(dataset, datasets.Dataset):
        identifier = extract_identifier(dataset.info)
    
    return identifier if identifier else f'unknown-{hash(str(dataset))}'
