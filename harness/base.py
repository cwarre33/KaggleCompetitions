"""
BaseTask Abstract Base Class defining the contract for all competition tasks.
"""
from abc import ABC, abstractmethod
from typing import Any, Tuple, Dict
import torch
from torch.utils.data import DataLoader


class BaseTask(ABC):
    """
    Abstract Base Task that all competition-specific tasks must inherit from.
    This ensures a consistent interface for the trainer.
    """

    @abstractmethod
    def get_model(self) -> torch.nn.Module:
        """
        Returns the model instance for this task.
        
        Returns:
            torch.nn.Module: The model to be trained/evaluated.
        """
        pass

    @abstractmethod
    def get_dataloaders(self) -> Tuple[DataLoader, DataLoader, DataLoader]:
        """
        Returns train, validation, and test dataloaders.
        
        Returns:
            Tuple[DataLoader, DataLoader, DataLoader]: 
                (train_loader, val_loader, test_loader)
        """
        pass

    @abstractmethod
    def compute_loss(self, outputs: Any, targets: Any, **kwargs) -> torch.Tensor:
        """
        Computes the loss given model outputs and targets.
        
        Args:
            outputs: Model outputs (can be tensor, dict, tuple depending on task)
            targets: Ground truth targets
            **kwargs: Additional task-specific arguments
            
        Returns:
            torch.Tensor: Computed loss tensor.
        """
        pass

    def get_optimizer(self, model: torch.nn.Module) -> torch.optim.Optimizer:
        """
        Optional: Returns optimizer for the model. Can be overridden for custom optimizers.
        
        Args:
            model: The model to optimize
            
        Returns:
            torch.optim.Optimizer: Optimizer instance
        """
        # Default optimizer - can be overridden
        return torch.optim.Adam(model.parameters(), lr=1e-3)

    def get_scheduler(self, optimizer: torch.optim.Optimizer) -> Any:
        """
        Optional: Returns learning rate scheduler. Can be overridden.
        
        Args:
            optimizer: The optimizer to schedule
            
        Returns:
            Any: Scheduler instance or None
        """
        return None