"""
Main Trainer class that orchestrates training using Hydra configuration.
Integrates with BaseTask, Augmentation, Distillation, and supports torch.compile.
"""
import hydra
from omegaconf import DictConfig, OmegaConf
import torch
import torch.nn as nn
from typing import Optional, Tuple, Any, Dict
import logging
from pathlib import Path
import yaml
import os
from harness.base import BaseTask
from harness.augmentation import create_augmentation_from_profile
from harness.distillation import create_distillation_wrapper, DistillationWrapper
from harness.artifacts import init_run, RunArtifacts

logger = logging.getLogger(__name__)


class HarnessTrainer:
    """
    Main trainer that orchestrates the training process.
    Uses Hydra for configuration management and integrates all harness components.
    """
    
    def __init__(self, config: DictConfig):
        """
        Initialize the trainer with Hydra configuration.
        
        Args:
            config: Hydra configuration object
        """
        self.config = config
        self.device = self._get_device()
        self.seed_everything(config.harness.seed)

        # Run artifacts (Kaggle-friendly, reproducible)
        try:
            competition_slug = str(getattr(getattr(config, "competition", {}), "slug", "unknown_competition"))
            repo_root = str(getattr(getattr(config, "paths", {}), "repo_root", "."))
            out_dir = str(getattr(getattr(config, "paths", {}), "out_dir", "auto"))
            self.run: RunArtifacts | None = init_run(
                competition=competition_slug,
                repo_root=repo_root,
                out_dir=out_dir,
                config_snapshot=config,
            )
        except Exception as e:
            logger.warning(f"Failed to init run artifacts: {e}")
            self.run = None
        
        # Initialize components
        self.task: Optional[BaseTask] = None
        self.model: Optional[nn.Module] = None
        self.student_model: Optional[nn.Module] = None
        self.teacher_model: Optional[nn.Module] = None
        self.distillation_wrapper: Optional[DistillationWrapper] = None
        self.augmentation_fn = None
        self.optimizer = None
        self.scheduler = None
        
        # Training state
        self.current_epoch = 0
        self.global_step = 0
        self.best_metric = float('inf')  # For minimization tasks
        
        # Setup logging
        self.setup_logging()
        
        logger.info(f"HarnessTrainer initialized with config:\n{OmegaConf.to_yaml(config)}")
    
    def _get_device(self) -> torch.device:
        """Get the appropriate device based on config and availability."""
        device_config = self.config.harness.device
        if device_config == "auto":
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            device = torch.device(device_config)
        logger.info(f"Using device: {device}")
        return device
    
    def seed_everything(self, seed: int):
        """Set random seeds for reproducibility."""
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        import numpy as np
        import random
        np.random.seed(seed)
        random.seed(seed)
        logger.info(f"Set random seed to {seed}")
    
    def setup_logging(self):
        """Setup logging configuration."""
        log_level = getattr(self.config.harness, 'log_level', 'INFO')
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def setup_task(self, task_class: type):
        """
        Setup the task (competition-specific implementation).
        
        Args:
            task_class: Class that inherits from BaseTask
        """
        logger.info(f"Setting up task: {task_class.__name__}")
        self.task = task_class()
        self.model = self.task.get_model()
        logger.info(f"Model: {self.model.__class__.__name__}")
    
    def setup_augmentation(self):
        """Setup augmentation from noise profile if enabled."""
        aug_config = self.config.augmentation
        if not aug_config.enabled or aug_config.noise_profile is None:
            logger.info("Augmentation disabled or no noise profile specified")
            self.augmentation_fn = None
            return
        
        logger.info(f"Setting up augmentation with profile: {aug_config.noise_profile}")
        try:
            repo_root = Path(getattr(getattr(self.config, "paths", {}), "repo_root", ".")).resolve()
            self.augmentation_fn = create_augmentation_from_profile(
                profile_name=aug_config.noise_profile,
                modality=aug_config.modality,
                profiles_dir=str(repo_root / "conf" / "noise_profiles")
            )
            logger.info("Augmentation setup complete")
        except Exception as e:
            logger.warning(f"Failed to setup augmentation: {e}")
            self.augmentation_fn = None
    
    def setup_distillation(self):
        """Setup distillation wrapper if enabled and teacher checkpoint provided."""
        distill_config = self.config.distillation
        if not distill_config.enabled or distill_config.teacher_checkpoint is None:
            logger.info("Distillation disabled or no teacher checkpoint provided")
            self.distillation_wrapper = None
            return
        
        logger.info(f"Setting up distillation from checkpoint: {distill_config.teacher_checkpoint}")
        try:
            # Load teacher model (simplified - in practice would load from checkpoint)
            # For now, we'll assume the task can provide a teacher or we load it
            if hasattr(self.task, 'get_teacher_model'):
                teacher_model = self.task.get_teacher_model()
            else:
                # Fallback: use student as teacher (no distillation)
                logger.warning("No teacher model available, using student as teacher")
                teacher_model = None
            
            if teacher_model is None:
                logger.warning("No teacher model available for distillation")
                self.distillation_wrapper = None
                return
            
            # Move teacher to device
            teacher_model = teacher_model.to(self.device)
            
            # Create distillation wrapper
            self.distillation_wrapper = create_distillation_wrapper(
                student=self.model,
                teacher=teacher_model,
                temperature=distill_config.temperature,
                alpha=distill_config.alpha
            )
            
            # Use the wrapper's student for training
            self.student_model = self.distillation_wrapper.get_student()
            logger.info("Distillation setup complete")
            
        except Exception as e:
            logger.warning(f"Failed to setup distillation: {e}")
            self.distillation_wrapper = None
    
    def setup_optimizer_scheduler(self):
        """Setup optimizer and learning rate scheduler."""
        opt_config = self.config.optimizer
        sched_config = self.config.scheduler
        
        # Setup optimizer
        if opt_config.type == "adam":
            self.optimizer = torch.optim.Adam(
                self.student_model.parameters() if self.distillation_wrapper else self.model.parameters(),
                lr=opt_config.lr,
                weight_decay=opt_config.weight_decay,
                betas=getattr(opt_config, 'betas', [0.9, 0.999]),
                eps=getattr(opt_config, 'eps', 1e-08)
            )
        elif opt_config.type == "sgd":
            self.optimizer = torch.optim.SGD(
                self.student_model.parameters() if self.distillation_wrapper else self.model.parameters(),
                lr=opt_config.lr,
                weight_decay=opt_config.weight_decay,
                momentum=getattr(opt_config, 'momentum', 0.9)
            )
        else:
            raise ValueError(f"Unsupported optimizer type: {opt_config.type}")
        
        logger.info(f"Optimizer: {opt_config.type} with lr={opt_config.lr}")
        
        # Setup scheduler
        if sched_config.type == "none":
            self.scheduler = None
        elif sched_config.type == "step":
            self.scheduler = torch.optim.lr_scheduler.StepLR(
                self.optimizer,
                step_size=sched_config.step_size,
                gamma=sched_config.gamma
            )
        elif sched_config.type == "cosine":
            self.scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
                self.optimizer,
                T_max=sched_config.T_max
            )
        elif sched_config.type == "plateau":
            self.scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
                self.optimizer,
                mode=sched_config.mode,
                factor=sched_config.factor,
                patience=sched_config.patience
            )
        else:
            raise ValueError(f"Unsupported scheduler type: {sched_config.type}")
        
        if self.scheduler is not None:
            logger.info(f"Scheduler: {sched_config.type}")
    
    def apply_compilation(self):
        """Apply torch.compile for performance optimization."""
        if self.config.harness.compile_model and hasattr(torch, 'compile'):
            logger.info("Applying torch.compile for performance optimization")
            model_to_compile = self.student_model if self.distillation_wrapper else self.model
            try:
                compiled_model = torch.compile(model_to_compile)
                if self.distillation_wrapper:
                    # Update the student model in the wrapper
                    self.distillation_wrapper.student = compiled_model
                    self.student_model = compiled_model
                else:
                    self.model = compiled_model
                logger.info("torch.compile applied successfully")
            except Exception as e:
                logger.warning(f"Failed to apply torch.compile: {e}")
        else:
            logger.info("torch.compile not applied (disabled or not available)")
    
    def train(self):
        """Main training loop."""
        if self.task is None:
            raise ValueError("Task not setup. Call setup_task() first.")
        
        # Setup data loaders
        train_loader, val_loader, test_loader = self.task.get_dataloaders()
        
        # Setup components
        self.setup_augmentation()
        self.setup_distillation()
        self.setup_optimizer_scheduler()
        self.apply_compilation()
        
        # Move models to device
        if self.distillation_wrapper:
            self.distillation_wrapper = self.distillation_wrapper.to(self.device)
        else:
            self.model = self.model.to(self.device)
        
        logger.info("Starting training...")
        logger.info(f"Max epochs: {self.config.trainer.max_epochs}")
        
        # Training loop
        for epoch in range(self.config.trainer.max_epochs):
            self.current_epoch = epoch
            self.train_epoch(train_loader)
            
            # Validation
            val_metrics = self.validate(val_loader)
            
            # Step scheduler if needed
            if self.scheduler is not None:
                if isinstance(self.scheduler, torch.optim.lr_scheduler.ReduceLROnPlateau):
                    self.scheduler.step(val_metrics.get('loss', 0.0))
                else:
                    self.scheduler.step()
            
            # Logging
            logger.info(f"Epoch {epoch}/{self.config.trainer.max_epochs-1} - Val Metrics: {val_metrics}")
            
            # Save best model (simplified)
            current_metric = val_metrics.get('loss', float('inf'))
            if current_metric < self.best_metric:
                self.best_metric = current_metric
                self.save_checkpoint(f"best_model_epoch_{epoch}.pt")
                logger.info(f"New best model saved with metric: {current_metric}")

            if self.run is not None:
                try:
                    self.run.save_metrics(
                        {
                            "epoch": int(epoch),
                            "val": {k: float(v) for k, v in val_metrics.items()},
                            "best_metric": float(self.best_metric),
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to write metrics.json: {e}")
        
        logger.info("Training completed!")
        return self.best_metric
    
    def train_epoch(self, train_loader):
        """Train for one epoch."""
        model_to_train = self.distillation_wrapper if self.distillation_wrapper else self.model
        model_to_train.train()
        
        epoch_loss = 0.0
        num_batches = 0
        
        for batch_idx, batch in enumerate(train_loader):
            # Unpack batch (assuming (inputs, targets) format)
            if isinstance(batch, (tuple, list)) and len(batch) >= 2:
                inputs, targets = batch[0], batch[1]
            else:
                inputs, targets = batch, None  # Handle cases where targets are in inputs
            
            # Move to device
            inputs = inputs.to(self.device)
            if targets is not None:
                targets = targets.to(self.device)
            
            # Apply augmentation if enabled
            if self.augmentation_fn is not None:
                inputs = self.augmentation_fn(inputs)
            
            # Zero gradients
            self.optimizer.zero_grad()
            
            # Forward pass
            if self.distillation_wrapper:
                outputs = self.distillation_wrapper(inputs)
                # For distillation, we need teacher outputs too
                with torch.no_grad():
                    teacher_outputs = self.distillation_wrapper.teacher(inputs) if self.distillation_wrapper.teacher else None
                
                # Compute loss
                if teacher_outputs is not None:
                    loss, hard_loss, distill_loss = self.distillation_wrapper.compute_distillation_loss(
                        outputs, teacher_outputs, targets
                    )
                else:
                    # Fallback to standard loss if no teacher
                    loss = self.task.compute_loss(outputs, targets)
            else:
                outputs = self.model(inputs)
                loss = self.task.compute_loss(outputs, targets)
            
            # Backward pass
            loss.backward()
            
            # Gradient clipping
            grad_clip_val = self.config.harness.gradient_clip_val
            if grad_clip_val > 0:
                torch.nn.utils.clip_grad_norm_(
                    model_to_train.parameters(), 
                    max_norm=grad_clip_val
                )
            
            # Optimizer step
            self.optimizer.step()
            
            # Update metrics
            epoch_loss += loss.item()
            num_batches += 1
            self.global_step += 1
            
            # Logging
            if batch_idx % self.config.harness.log_every_n_steps == 0:
                logger.info(
                    f"Epoch {self.current_epoch}, Batch {batch_idx}/{len(train_loader)}, "
                    f"Loss: {loss.item():.4f}"
                )
        
        avg_epoch_loss = epoch_loss / max(num_batches, 1)
        logger.info(f"Epoch {self.current_epoch} Average Loss: {avg_epoch_loss:.4f}")
    
    def validate(self, val_loader) -> Dict[str, float]:
        """Validate the model."""
        model_to_eval = self.distillation_wrapper if self.distillation_wrapper else self.model
        model_to_eval.eval()
        
        val_loss = 0.0
        num_batches = 0
        
        with torch.no_grad():
            for batch in val_loader:
                # Unpack batch
                if isinstance(batch, (tuple, list)) and len(batch) >= 2:
                    inputs, targets = batch[0], batch[1]
                else:
                    inputs, targets = batch, None
                
                # Move to device
                inputs = inputs.to(self.device)
                if targets is not None:
                    targets = targets.to(self.device)
                
                # Forward pass
                outputs = model_to_eval(inputs)
                loss = self.task.compute_loss(outputs, targets)
                
                val_loss += loss.item()
                num_batches += 1
        
        avg_val_loss = val_loss / max(num_batches, 1)
        return {"loss": avg_val_loss}
    
    def save_checkpoint(self, filename: str):
        """Save model checkpoint."""
        if self.run is not None:
            checkpoint_path = self.run.model_dir / filename
            checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            checkpoint_dir = Path("checkpoints")
            checkpoint_dir.mkdir(exist_ok=True)
            checkpoint_path = checkpoint_dir / filename
        
        checkpoint = {
            'epoch': self.current_epoch,
            'global_step': self.global_step,
            'best_metric': self.best_metric,
            'config': OmegaConf.to_container(self.config, resolve=True),
        }
        
        if self.distillation_wrapper:
            checkpoint['student_state_dict'] = self.distillation_wrapper.student.state_dict()
            if self.distillation_wrapper.teacher is not None:
                checkpoint['teacher_state_dict'] = self.distillation_wrapper.teacher.state_dict()
        else:
            checkpoint['model_state_dict'] = self.model.state_dict()
        
        checkpoint['optimizer_state_dict'] = self.optimizer.state_dict()
        if self.scheduler is not None:
            checkpoint['scheduler_state_dict'] = self.scheduler.state_dict()
        
        torch.save(checkpoint, checkpoint_path)
        logger.info(f"Checkpoint saved: {checkpoint_path}")
    
    def load_checkpoint(self, checkpoint_path: str):
        """Load model checkpoint."""
        checkpoint = torch.load(checkpoint_path, map_location=self.device)
        
        self.current_epoch = checkpoint['epoch']
        self.global_step = checkpoint['global_step']
        self.best_metric = checkpoint['best_metric']
        
        if self.distillation_wrapper:
            self.distillation_wrapper.student.load_state_dict(checkpoint['student_state_dict'])
            if 'teacher_state_dict' in checkpoint and self.distillation_wrapper.teacher is not None:
                self.distillation_wrapper.teacher.load_state_dict(checkpoint['teacher_state_dict'])
        else:
            self.model.load_state_dict(checkpoint['model_state_dict'])
        
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        if self.scheduler is not None and 'scheduler_state_dict' in checkpoint:
            self.scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
        
        logger.info(f"Checkpoint loaded: {checkpoint_path}")


@hydra.main(config_path="conf", config_name="global_defaults", version_base=None)
def main(cfg: DictConfig) -> None:
    """
    Main entry point for hydra execution.
    This function is called by Hydra with the composed configuration.
    """
    # This is a placeholder - actual usage would involve importing a specific task
    logger.info("HarnessTrainer main function called")
    logger.info(f"Configuration:\n{OmegaConf.to_yaml(cfg)}")
    # In practice, you would instantiate your task here and run training
    # Example:
    # from my_competition.task import MyCompetitionTask
    # trainer = HarnessTrainer(cfg)
    # trainer.setup_task(MyCompetitionTask)
    # trainer.train()


if __name__ == "__main__":
    main()