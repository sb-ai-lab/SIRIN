from typing import List, Optional, Tuple

import torch
import torch.nn as nn


class Identity(nn.Module):
    def __init__(self):
        super(Identity, self).__init__()

    def forward(self, x):
        return x


class LinearClassifier(nn.Module):
    def __init__(
        self,
        embedding_dim: List[int],
        num_features: List[int],
        attention_pooling: List[bool],
        ensemble: List[int],
        num_classes: int = 1,
        use_contrastive: bool = True,
        projection_dim: int = 128,
        contrastive_layers: Optional[List[int]] = None,
        projection_hidden_dim: Optional[int] = None,
        projection_num_layers: int = 2,
        use_projection_dropout: bool = False,
        projection_dropout: float = 0.1,
    ):
        super().__init__()
        
        self.use_contrastive = use_contrastive
        self.projection_dim = projection_dim
        self.projection_hidden_dim = projection_hidden_dim
        self.projection_num_layers = projection_num_layers
        self.use_projection_dropout = use_projection_dropout
        self.projection_dropout = projection_dropout
        
        self.contrastive_layers = contrastive_layers or range(len(embedding_dim)) 
        
        self.q = nn.ModuleList([])
        self.attention_pooling = attention_pooling

        self.layer_classifiers = nn.ModuleList([Identity() for _ in embedding_dim])

        for i in ensemble:
            self.layer_classifiers[i] = nn.Linear(
                embedding_dim[i] * num_features[i], num_classes
            )
        
        non_ensemble_size = sum([
            embedding_dim[i] * num_features[i]
            for i in range(len(num_features))
            if i not in ensemble
        ])
        ensemble_size = len(ensemble)
        self.final_vector_size = non_ensemble_size + ensemble_size
        
        self.classifier = nn.Linear(self.final_vector_size, num_classes)
        
        if self.use_contrastive:
            self.projection_head = self._build_projection_head()
        
        for e_d, n_f in zip(embedding_dim, num_features):
            queries = nn.ParameterList()
            for i in range(n_f):
                query = nn.Parameter(torch.empty(1, 1, e_d))
                nn.init.xavier_uniform_(query)
                queries.append(query)
            self.q.append(queries)
    
    def _build_projection_head(self) -> nn.Module:
        """Builds multi-layer projection head for contrastive learning."""
        projection_layers = []
        
        projection_input_dim = self.final_vector_size
        hidden_dim = self.projection_hidden_dim or (projection_input_dim // 2)
        
        # First layer
        projection_layers.append(nn.Linear(projection_input_dim, hidden_dim))
        projection_layers.append(nn.BatchNorm1d(hidden_dim))
        projection_layers.append(nn.ReLU(inplace=True))
        
        if self.use_projection_dropout:
            projection_layers.append(nn.Dropout(self.projection_dropout))
        
        # Middle layers (if num_layers > 2)
        for _ in range(self.projection_num_layers - 2):
            projection_layers.append(nn.Linear(hidden_dim, hidden_dim))
            projection_layers.append(nn.BatchNorm1d(hidden_dim))
            projection_layers.append(nn.ReLU(inplace=True))
            
            if self.use_projection_dropout:
                projection_layers.append(nn.Dropout(self.projection_dropout))
        
        # Final projection layer
        projection_layers.append(nn.Linear(hidden_dim, self.projection_dim))
        
        return nn.Sequential(*projection_layers)
    
    def _extract_contrastive_features(
        self,
        hiddens_list: List[torch.Tensor],
        attention_masks_list: List[torch.Tensor] = None,
    ) -> torch.Tensor:
        contrastive_features = []
        
        for layer_idx in self.contrastive_layers:
            if layer_idx < len(hiddens_list):
                hiddens = hiddens_list[layer_idx]
                attention_masks = attention_masks_list[layer_idx] if attention_masks_list else None
                
                layer_features = self._pool_layer_features(
                    hiddens, attention_masks, layer_idx
                )
                contrastive_features.append(layer_features)
        
        if not contrastive_features:
            return None
        
        if len(contrastive_features) > 1:
            contrastive_features = torch.cat(contrastive_features, dim=-1)
        else:
            contrastive_features = contrastive_features[0]
        
        return contrastive_features
    
    def _pool_layer_features(
        self,
        hiddens: torch.Tensor,
        attention_masks: Optional[torch.Tensor],
        layer_idx: int,
    ) -> torch.Tensor:
        features = []
        
        for i, query in enumerate(self.q[layer_idx]):
            hidden = hiddens[:, i]
            
            if self.attention_pooling[layer_idx]:
                attention_scores = torch.matmul(hidden, query.transpose(-1, -2)).squeeze(-1)
                
                if attention_masks is not None:
                    attention_mask = attention_masks[:, i]
                    attention_scores = attention_scores.masked_fill(
                        attention_mask == 0, float('-inf')
                    )
                
                attention_weights = torch.nn.functional.softmax(attention_scores, dim=-1)
                pooled = torch.sum(hidden * attention_weights.unsqueeze(-1), dim=1)
            else:
                if attention_masks is not None:
                    attention_mask = attention_masks[:, i]
                    mask_expanded = attention_mask.unsqueeze(-1)
                    hidden_masked = hidden * mask_expanded
                    sum_pooled = torch.sum(hidden_masked, dim=1)
                    lengths = torch.sum(mask_expanded, dim=1)
                    pooled = sum_pooled / lengths.clamp(min=1e-9)
                else:
                    pooled = torch.mean(hidden, dim=1)
            
            features.append(pooled)
        
        layer_features = torch.cat(features, dim=-1)
        return layer_features
    
    def forward(
        self,
        hiddens_list: List[torch.Tensor],
        attention_masks_list: List[torch.Tensor] = None,
        return_projection: bool = False,
        **kwargs,
    ) -> torch.Tensor:
        final = []
        
        for index, (hiddens, attention_masks) in enumerate(zip(hiddens_list, attention_masks_list)):
            context = []
            for i, query in enumerate(self.q[index]):
                hidden = hiddens[:, i]
                attention_mask = (
                    attention_masks[:, i]
                    if attention_masks is not None
                    else torch.ones(hidden.shape[:2])
                )

                if self.attention_pooling[index]:
                    attention_scores = torch.matmul(
                        hidden, query.transpose(-1, -2)
                    ).squeeze(-1)
                    if attention_masks is not None:
                        attention_mask = attention_masks[:, i]
                        attention_scores = attention_scores.masked_fill(
                            attention_mask == 0, float('-inf')
                        )
                    attention_weights = torch.nn.functional.softmax(
                        attention_scores, dim=-1
                    )
                    hidden = torch.sum(
                        hidden * attention_weights.unsqueeze(-1), dim=1
                    )

                if hidden.ndim == 4:
                    valid_counts = attention_mask.sum(dim=1)
                    last_valid_idx = valid_counts - 1
                    hidden = hidden[:, last_valid_idx, :]

                hidden = self.layer_classifiers[index](hidden)
                context.append(hidden)

            context_vector = torch.concat(context, dim=1)
            final.append(context_vector)
        
        final_vector = torch.cat(final, dim=-1)
        logits = self.classifier(final_vector.float())
        
        if self.use_contrastive and return_projection:
            # Get projection for contrastive loss
            projection = self.get_contrastive_projection(
                hiddens_list, attention_masks_list
            )
            return projection, logits
        
        return logits
    
    def get_contrastive_projection(
        self,
        hiddens_list: List[torch.Tensor],
        attention_masks_list: List[torch.Tensor] = None,
    ) -> torch.Tensor:
        if not self.use_contrastive:
            raise ValueError('Model was not initialized with use_contrastive=True')
        
        contrastive_features = self._extract_contrastive_features(
            hiddens_list, attention_masks_list
        )
        
        if contrastive_features is None:
            final_vector = self._get_final_vector(hiddens_list, attention_masks_list)
            projection = self.projection_head(final_vector)
        else:
            projection = self.projection_head(contrastive_features)
        
        return projection
    
    def forward_with_projection(
        self,
        hiddens_list: List[torch.Tensor],
        attention_masks_list: List[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        return self.forward(
            hiddens_list,
            attention_masks_list,
            return_projection=True
        )
    
    def _get_final_vector(
        self,
        hiddens_list: List[torch.Tensor],
        attention_masks_list: List[torch.Tensor] = None,
    ) -> torch.Tensor:
        final = []
        
        for index, (hiddens, attention_masks) in enumerate(zip(hiddens_list, attention_masks_list)):
            context = []
            for i, query in enumerate(self.q[index]):
                hidden = hiddens[:, i]
                attention_mask = (
                    attention_masks[:, i]
                    if attention_masks is not None
                    else torch.ones(hidden.shape[:2])
                )

                if self.attention_pooling[index]:
                    attention_scores = torch.matmul(
                        hidden, query.transpose(-1, -2)
                    ).squeeze(-1)
                    if attention_masks is not None:
                        attention_mask = attention_masks[:, i]
                        attention_scores = attention_scores.masked_fill(
                            attention_mask == 0, float('-inf')
                        )
                    attention_weights = torch.nn.functional.softmax(
                        attention_scores, dim=-1
                    )
                    hidden = torch.sum(
                        hidden * attention_weights.unsqueeze(-1), dim=1
                    )

                if hidden.ndim == 4:
                    valid_counts = attention_mask.sum(dim=1)
                    last_valid_idx = valid_counts - 1
                    hidden = hidden[:, last_valid_idx, :]

                context.append(hidden)

            context_vector = torch.concat(context, dim=1)
            final.append(context_vector)
        
        final_vector = torch.cat(final, dim=-1)
        return final_vector
    
    def get_layer_features(
        self,
        hiddens_list: List[torch.Tensor],
        attention_masks_list: List[torch.Tensor] = None,
        layer_indices: Optional[List[int]] = None,
    ) -> List[torch.Tensor]:
        """
        Extracts features at specified layers for multi-level contrastive learning.
        
        Args:
            hiddens_list: List of hidden states from different layers
            attention_masks_list: List of attention masks
            layer_indices: Indices of layers to extract features from (None = all layers)
        
        Returns:
            List of feature tensors, one per specified layer
        """
        if layer_indices is None:
            layer_indices = list(range(len(hiddens_list)))
        
        layer_features = []
        
        for layer_idx in layer_indices:
            if layer_idx >= len(hiddens_list):
                continue
                
            hiddens = hiddens_list[layer_idx]
            attention_masks = attention_masks_list[layer_idx] if attention_masks_list else None
            
            # Pool features for this layer
            features = self._pool_layer_features(hiddens, attention_masks, layer_idx)
            layer_features.append(features)
        
        return layer_features