from typing import List

import torch

from sirin.definitions import INPUT_COL, TARGET_COL


class FeaturesDataset(torch.utils.data.Dataset):
    def __init__(self, data_dict):
        self.data = {key: value.detach().clone() if isinstance(value, torch.Tensor) else torch.tensor(value) for key, value in data_dict.items()}
        self.length = len(next(iter(data_dict.values())))

    def __len__(self):
        return self.length

    def __getitem__(self, idx):
        return {key: value[idx] for key, value in self.data.items()}


class InputsDataset(torch.utils.data.Dataset):
    def __init__(self, input, target, group_ids=None):
        self.input = input
        self.target = target
        self.group_ids = group_ids

    def __len__(self):
        return len(self.input)

    def __getitem__(self, idx):
        if isinstance(idx, (list, slice)):
            if isinstance(idx, slice):
                indices = list(range(*idx.indices(len(self))))
            else:
                indices = idx
            
            batch = {
                INPUT_COL: [self.input[i] for i in indices],
                TARGET_COL: [self.target[i] for i in indices]
            }
            if self.group_ids is not None:
                batch['group_ids'] = [self.group_ids[i] for i in indices]
            return batch
        elif isinstance(idx, str):
            if idx == INPUT_COL:
                return self.input
            else:
                return self.target
        else:
            item = {
                INPUT_COL: self.input[idx],
                TARGET_COL: self.target[idx]
            }
            if self.group_ids is not None:
                item['group_ids'] = self.group_ids[idx]
            return item

    def batch_process(self, preprocess_func, batch_size: int = 32, remove_columns: List[str] = None):
        """
        Process the dataset in batches using the provided preprocessing function
        """
        if remove_columns is None:
            remove_columns = []
            
        all_processed = {}
        
        for i in range(0, len(self), batch_size):
            batch_indices = list(range(i, min(i + batch_size, len(self))))
            batch = self[batch_indices]
            
            processed_batch = preprocess_func(batch)
            
            for key in processed_batch:
                if key not in all_processed:
                    all_processed[key] = []
                all_processed[key].extend(processed_batch[key])
        
        for col in remove_columns:
            if col in all_processed:
                del all_processed[col]
        
        return all_processed
