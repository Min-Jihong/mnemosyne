from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json


@dataclass
class TrainingConfig:
    model_name: str = "behavior_transformer"
    batch_size: int = 32
    learning_rate: float = 1e-4
    epochs: int = 100
    context_length: int = 5
    hidden_dim: int = 256
    num_heads: int = 8
    num_layers: int = 4
    dropout: float = 0.1
    checkpoint_dir: Path = Path("checkpoints")
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "model_name": self.model_name,
            "batch_size": self.batch_size,
            "learning_rate": self.learning_rate,
            "epochs": self.epochs,
            "context_length": self.context_length,
            "hidden_dim": self.hidden_dim,
            "num_heads": self.num_heads,
            "num_layers": self.num_layers,
            "dropout": self.dropout,
            "checkpoint_dir": str(self.checkpoint_dir),
        }


class BehaviorTrainer:
    
    def __init__(self, config: TrainingConfig | None = None):
        self.config = config or TrainingConfig()
        self._model = None
        self._optimizer = None
        self._device = None
    
    def _check_torch(self) -> None:
        try:
            import torch
            self._device = torch.device(
                "mps" if torch.backends.mps.is_available()
                else "cuda" if torch.cuda.is_available()
                else "cpu"
            )
        except ImportError:
            raise ImportError(
                "PyTorch is required for training. "
                "Install with: pip install torch"
            )
    
    def prepare_data(self, data_dir: Path | str) -> "torch.utils.data.DataLoader":
        self._check_torch()
        import torch
        from torch.utils.data import Dataset, DataLoader
        
        data_dir = Path(data_dir)
        
        class BehaviorDatasetTorch(Dataset):
            def __init__(self, data_dir: Path):
                self.samples = []
                for jsonl_file in data_dir.glob("*.jsonl"):
                    with open(jsonl_file) as f:
                        for line in f:
                            self.samples.append(json.loads(line))
            
            def __len__(self):
                return len(self.samples)
            
            def __getitem__(self, idx):
                sample = self.samples[idx]
                return {
                    "action_type": sample["action_type"],
                    "window_app": sample["window_app"],
                    "context": sample["context_events"],
                }
        
        dataset = BehaviorDatasetTorch(data_dir)
        return DataLoader(
            dataset,
            batch_size=self.config.batch_size,
            shuffle=True,
        )
    
    def build_model(self, vocab_size: int, num_actions: int) -> "torch.nn.Module":
        self._check_torch()
        import torch
        import torch.nn as nn
        
        class BehaviorTransformer(nn.Module):
            def __init__(
                self,
                vocab_size: int,
                num_actions: int,
                hidden_dim: int,
                num_heads: int,
                num_layers: int,
                dropout: float,
            ):
                super().__init__()
                self.embedding = nn.Embedding(vocab_size, hidden_dim)
                
                encoder_layer = nn.TransformerEncoderLayer(
                    d_model=hidden_dim,
                    nhead=num_heads,
                    dim_feedforward=hidden_dim * 4,
                    dropout=dropout,
                    batch_first=True,
                )
                self.transformer = nn.TransformerEncoder(
                    encoder_layer,
                    num_layers=num_layers,
                )
                
                self.action_head = nn.Linear(hidden_dim, num_actions)
                self.position_head = nn.Linear(hidden_dim, 2)
            
            def forward(self, x):
                x = self.embedding(x)
                x = self.transformer(x)
                pooled = x.mean(dim=1)
                
                action_logits = self.action_head(pooled)
                position = self.position_head(pooled)
                
                return action_logits, position
        
        self._model = BehaviorTransformer(
            vocab_size=vocab_size,
            num_actions=num_actions,
            hidden_dim=self.config.hidden_dim,
            num_heads=self.config.num_heads,
            num_layers=self.config.num_layers,
            dropout=self.config.dropout,
        ).to(self._device)
        
        return self._model
    
    def train(
        self,
        dataloader: "torch.utils.data.DataLoader",
        vocab_size: int = 10000,
        num_actions: int = 20,
    ) -> dict[str, list[float]]:
        self._check_torch()
        import torch
        import torch.nn as nn
        
        if self._model is None:
            self.build_model(vocab_size, num_actions)
        
        self._optimizer = torch.optim.AdamW(
            self._model.parameters(),
            lr=self.config.learning_rate,
        )
        
        criterion = nn.CrossEntropyLoss()
        history = {"loss": [], "accuracy": []}
        
        self.config.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        for epoch in range(self.config.epochs):
            self._model.train()
            epoch_loss = 0.0
            correct = 0
            total = 0
            
            for batch in dataloader:
                self._optimizer.zero_grad()
                
                inputs = torch.randint(
                    0, vocab_size,
                    (len(batch["action_type"]), self.config.context_length)
                ).to(self._device)
                
                targets = torch.randint(0, num_actions, (len(batch["action_type"]),)).to(self._device)
                
                action_logits, _ = self._model(inputs)
                loss = criterion(action_logits, targets)
                
                loss.backward()
                self._optimizer.step()
                
                epoch_loss += loss.item()
                _, predicted = action_logits.max(1)
                correct += (predicted == targets).sum().item()
                total += targets.size(0)
            
            avg_loss = epoch_loss / len(dataloader)
            accuracy = correct / total if total > 0 else 0
            
            history["loss"].append(avg_loss)
            history["accuracy"].append(accuracy)
            
            if (epoch + 1) % 10 == 0:
                self.save_checkpoint(epoch + 1)
        
        return history
    
    def save_checkpoint(self, epoch: int) -> Path:
        self._check_torch()
        import torch
        
        checkpoint_path = self.config.checkpoint_dir / f"model_epoch_{epoch}.pt"
        torch.save({
            "epoch": epoch,
            "model_state_dict": self._model.state_dict(),
            "optimizer_state_dict": self._optimizer.state_dict(),
            "config": self.config.to_dict(),
        }, checkpoint_path)
        
        return checkpoint_path
    
    def load_checkpoint(self, checkpoint_path: Path | str) -> None:
        self._check_torch()
        import torch
        
        checkpoint = torch.load(checkpoint_path, map_location=self._device)
        
        if self._model is not None:
            self._model.load_state_dict(checkpoint["model_state_dict"])
        
        if self._optimizer is not None:
            self._optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
