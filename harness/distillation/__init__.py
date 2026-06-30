"""
Distillation Engine implementing teacher-student knowledge distillation.
Supports optional teacher with KL-Divergence loss, temperature scaling, and alpha weighting.
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Tuple, Any


class DistillationWrapper(nn.Module):
    """
    Wrapper for knowledge distillation that combines student and optional teacher models.
    Implements KL-Divergence loss with configurable temperature (T) and alpha (α) weighting.
    If no teacher is provided, defaults to standard supervised training.
    """
    
    def __init__(
        self, 
        student: nn.Module, 
        teacher: Optional[nn.Module] = None,
        temperature: float = 1.0,
        alpha: float = 0.5,
        hard_loss_fn: Optional[callable] = None
    ):
        """
        Initialize the DistillationWrapper.
        
        Args:
            student: Student model to be trained
            teacher: Optional teacher model (if None, uses standard training)
            temperature: Temperature for softening probability distributions (T > 0)
            alpha: Weight for distillation loss (1-alpha weights hard target loss)
            hard_loss_fn: Loss function for hard targets (defaults to CrossEntropyLoss)
        """
        super().__init__()
        self.student = student
        self.teacher = teacher
        self.temperature = temperature
        self.alpha = alpha
        
        # Set teacher to eval mode if provided (no gradient updates)
        if self.teacher is not None:
            self.teacher.eval()
            for param in self.teacher.parameters():
                param.requires_grad = False
        
        # Default hard loss function
        self.hard_loss_fn = hard_loss_fn or nn.CrossEntropyLoss()
        
        # KL divergence loss for soft targets
        self.kl_loss_fn = nn.KLDivLoss(reduction='batchmean')
    
    def forward(self, *args, **kwargs) -> Any:
        """
        Forward pass through the student model.
        
        Returns:
            Student model outputs
        """
        return self.student(*args, **kwargs)
    
    def compute_distillation_loss(
        self, 
        student_outputs: Any, 
        teacher_outputs: Any, 
        targets: Any
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Compute distillation loss components.
        
        Args:
            student_outputs: Outputs from student model
            teacher_outputs: Outputs from teacher model (ignored if teacher is None)
            targets: Ground truth targets
            
        Returns:
            Tuple of (total_loss, hard_loss, distillation_loss)
        """
        # If no teacher, return standard supervised loss
        if self.teacher is None:
            hard_loss = self.hard_loss_fn(student_outputs, targets)
            return hard_loss, hard_loss, torch.tensor(0.0, device=hard_loss.device)
        
        # Compute hard loss (student vs ground truth)
        hard_loss = self.hard_loss_fn(student_outputs, targets)
        
        # Compute soft loss (student vs teacher) with temperature scaling
        # Ensure outputs are logits for proper softmax
        student_logits = student_outputs
        teacher_logits = teacher_outputs
        
        # Soften probabilities with temperature
        student_soft = F.log_softmax(student_logits / self.temperature, dim=-1)
        teacher_soft = F.softmax(teacher_logits / self.temperature, dim=-1)
        
        # KL divergence loss
        distillation_loss = self.kl_loss_fn(student_soft, teacher_soft) * (self.temperature ** 2)
        
        # Combine losses
        total_loss = self.alpha * distillation_loss + (1 - self.alpha) * hard_loss
        
        return total_loss, hard_loss, distillation_loss
    
    def get_student(self) -> nn.Module:
        """Get the student model."""
        return self.student
    
    def get_teacher(self) -> Optional[nn.Module]:
        """Get the teacher model (may be None)."""
        return self.teacher


def create_distillation_wrapper(
    student: nn.Module,
    teacher: Optional[nn.Module] = None,
    temperature: float = 1.0,
    alpha: float = 0.5,
    hard_loss_fn: Optional[callable] = None
) -> DistillationWrapper:
    """
    Factory function to create a DistillationWrapper.
    
    Args:
        student: Student model
        teacher: Optional teacher model
        temperature: Temperature for softening (T > 0)
        alpha: Weight for distillation loss [0,1]
        hard_loss_fn: Loss function for hard targets
        
    Returns:
        DistillationWrapper instance
    """
    return DistillationWrapper(
        student=student,
        teacher=teacher,
        temperature=temperature,
        alpha=alpha,
        hard_loss_fn=hard_loss_fn
    )


# Example usage:
# wrapper = create_distillation_wrapper(student_model, teacher_model, T=2.0, alpha=0.7)
# outputs = wrapper(inputs)
# loss, hard_loss, distill_loss = wrapper.compute_distillation_loss(outputs, teacher_outputs, targets)