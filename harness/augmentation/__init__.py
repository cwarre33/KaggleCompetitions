"""
Augmentation Registry and Factory for MAI-inspired synthetic noise generation.
Supports acoustic, visual, and logical augmentations via noise profiles.
"""
import yaml
from typing import Dict, Any, Callable, List, Optional
from functools import wraps
import torch
import numpy as np
from pathlib import Path

# Optional deps: keep import-time lightweight so sklearn-only harness usage
# doesn't require torchvision/torchaudio to be installed and compatible.
try:
    import torchvision.transforms as T  # type: ignore
except Exception:  # pragma: no cover
    T = None

try:
    import torchaudio.transforms as AT  # type: ignore
except Exception:  # pragma: no cover
    AT = None


class AugmentationRegistry:
    """
    Registry for augmentation transforms. Uses decorator-based registration.
    """
    def __init__(self):
        self._registry: Dict[str, Callable] = {}

    def register(self, name: str):
        """
        Decorator to register an augmentation function.
        
        Args:
            name: Unique name for the augmentation
        """
        def decorator(func: Callable):
            self._registry[name] = func
            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper
        return decorator

    def get(self, name: str) -> Callable:
        """
        Retrieve an augmentation function by name.
        
        Args:
            name: Name of the augmentation
            
        Returns:
            Callable: The augmentation function
            
        Raises:
            KeyError: If augmentation not found
        """
        if name not in self._registry:
            raise KeyError(f"Augmentation '{name}' not found in registry")
        return self._registry[name]

    def list_augmentations(self) -> List[str]:
        """Return list of registered augmentation names."""
        return list(self._registry.keys())


# Global registries for different modalities
acoustic_registry = AugmentationRegistry()
visual_registry = AugmentationRegistry()
logic_registry = AugmentationRegistry()


def load_noise_profile(profile_path: str) -> Dict[str, Any]:
    """
    Load a noise profile from YAML file.
    
    Args:
        profile_path: Path to the YAML noise profile
        
    Returns:
        Dict containing the noise profile configuration
    """
    with open(profile_path, 'r') as f:
        profile = yaml.safe_load(f)
    return profile


class NoiseProfileStack:
    """
    Stacks multiple augmentations based on a noise profile configuration.
    """
    def __init__(self, profile: Dict[str, Any], modality: str = "acoustic"):
        """
        Initialize noise profile stack.
        
        Args:
            profile: Noise profile configuration dictionary
            modality: Type of modality ('acoustic', 'visual', 'logic')
        """
        self.modality = modality
        self.augmentations = []
        
        # Select appropriate registry
        if modality == "acoustic":
            registry = acoustic_registry
        elif modality == "visual":
            registry = visual_registry
        elif modality == "logic":
            registry = logic_registry
        else:
            raise ValueError(f"Unknown modality: {modality}")
        
        # Build augmentation stack from profile
        for aug_name, aug_params in profile.get("augmentations", {}).items():
            if aug_params.get("enabled", True):
                aug_func = registry.get(aug_name)
                self.augmentations.append((aug_func, aug_params.get("params", {})))

    def __call__(self, data: Any) -> Any:
        """
        Apply all augmentations in the stack to the input data.
        
        Args:
            data: Input data to augment
            
        Returns:
            Augmented data
        """
        augmented_data = data
        for aug_func, params in self.augmentations:
            augmented_data = aug_func(augmented_data, **params)
        return augmented_data


# Example augmentation implementations (to be expanded)
@acoustic_registry.register("codec_distortion")
def codec_distortion(audio: torch.Tensor, bitrate: float = 128.0) -> torch.Tensor:
    """
    Simulate codec distortion by quantization noise.
    Simplified implementation - in practice would use actual codecs.
    """
    # Add quantization noise proportional to (1 - bitrate/320)
    noise_level = max(0.0, 1.0 - bitrate/320.0)
    noise = torch.randn_like(audio) * noise_level * 0.1
    return audio + noise


@acoustic_registry.register("rir")
def add_reverb(audio: torch.Tensor, reverberance: float = 0.3) -> torch.Tensor:
    """
    Add reverberation using simplified early reflections model.
    """
    # Simple echo effect
    delay = int(0.05 * 16000)  # 50ms delay at 16kHz
    if delay < audio.shape[-1]:
        echo = torch.zeros_like(audio)
        echo[..., delay:] = audio[..., :-delay] * reverberance
        return audio + echo
    return audio


@acoustic_registry.register("background_babble")
def add_background_babble(audio: torch.Tensor, snr_db: float = 10.0) -> torch.Tensor:
    """
    Add background babble noise at specified SNR.
    """
    signal_power = audio.pow(2).mean()
    noise_power = signal_power / (10 ** (snr_db / 10))
    noise = torch.randn_like(audio) * np.sqrt(noise_power)
    return audio + noise


@visual_registry.register("compression_artifacts")
def add_compression_artifacts(image: torch.Tensor, quality: int = 20) -> torch.Tensor:
    """
    Simulate JPEG compression artifacts.
    Simplified implementation.
    """
    # Add high-frequency noise inversely proportional to quality
    noise_level = (100 - quality) / 100.0
    noise = torch.randn_like(image) * noise_level * 0.1
    return torch.clamp(image + noise, 0., 1.)


@visual_registry.register("motion_blur")
def add_motion_blur(image: torch.Tensor, kernel_size: int = 5) -> torch.Tensor:
    """
    Add motion blur using simple horizontal blur.
    """
    # Simple box blur approximation
    padding = kernel_size // 2
    blurred = torch.nn.functional.avg_pool2d(
        image.unsqueeze(0), 
        kernel_size=(1, kernel_size), 
        stride=1, 
        padding=(0, padding)
    ).squeeze(0)
    return blurred


@visual_registry.register("sensor_noise")
def add_sensor_noise(image: torch.Tensor, noise_level: float = 0.01) -> torch.Tensor:
    """
    Add sensor noise (Gaussian noise).
    """
    noise = torch.randn_like(image) * noise_level
    return torch.clamp(image + noise, 0., 1.)


@logic_registry.register("token_dropout")
def token_dropout(tokens: torch.Tensor, dropout_prob: float = 0.1) -> torch.Tensor:
    """
    Randomly drop tokens (replace with mask/pad token).
    """
    mask = torch.rand_like(tokens.float()) < dropout_prob
    # Assuming 0 is pad token - in practice would use actual pad token id
    return tokens.masked_fill(mask, 0)


@logic_registry.register("synonym_replacement")
def synonym_replacement(tokens: torch.Tensor, replacement_prob: float = 0.1) -> torch.Tensor:
    """
    Simplified synonym replacement - in practice would use embedding similarity.
    For now, just adds small random noise to embeddings.
    """
    if tokens.dtype != torch.float32:
        # Assume token IDs, convert to embeddings simulation
        noise = torch.randn_like(tokens.float()) * replacement_prob * 0.1
        return tokens + noise.long()
    else:
        noise = torch.randn_like(tokens) * replacement_prob * 0.1
        return tokens + noise


def create_augmentation_from_profile(profile_name: str, modality: str = "acoustic", 
                                   profiles_dir: str = "conf/noise_profiles") -> NoiseProfileStack:
    """
    Factory function to create augmentation stack from a named profile.
    
    Args:
        profile_name: Name of the noise profile (without .yaml extension)
        modality: Type of modality ('acoustic', 'visual', 'logic')
        profiles_dir: Directory containing noise profile YAML files
        
    Returns:
        NoiseProfileStack: Configured augmentation stack
    """
    profile_path = Path(profiles_dir) / f"{profile_name}.yaml"
    if not profile_path.exists():
        raise FileNotFoundError(f"Noise profile not found: {profile_path}")
    
    profile = load_noise_profile(str(profile_path))
    return NoiseProfileStack(profile, modality=modality)


# Example usage would be:
# acoustic_aug = create_augmentation_from_profile("call_center", "acoustic")
# augmented_audio = acoustic_aug(raw_audio)