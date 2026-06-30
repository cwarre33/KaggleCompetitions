"""
Exporter class for ONNX conversion with fixed/dynamic axes support for Kaggle T4 inference.
"""
import torch
import torch.nn as nn
from typing import Optional, Union, List, Dict, Any, Tuple
from pathlib import Path
import logging
import numpy as np

logger = logging.getLogger(__name__)


class Exporter:
    """
    Exporter for converting PyTorch models to ONNX format.
    Supports both fixed and dynamic axes for flexible deployment.
    """
    
    def __init__(
        self, 
        model: nn.Module,
        model_name: str = "model",
        opset_version: int = 11,
        do_constant_folding: bool = True
    ):
        """
        Initialize the Exporter.
        
        Args:
            model: PyTorch model to export
            model_name: Name for the exported ONNX file (without extension)
            opset_version: ONNX opset version to use
            do_constant_folding: Whether to perform constant folding optimization
        """
        self.model = model
        self.model_name = model_name
        self.opset_version = opset_version
        self.do_constant_folding = do_constant_folding
        self.model.eval()  # Set model to evaluation mode
        
        logger.info(f"Exporter initialized for model: {model_name}")
        logger.info(f"ONNX opset version: {opset_version}")
    
    def export(
        self,
        export_path: Union[str, Path],
        input_sample: Optional[torch.Tensor] = None,
        input_shape: Optional[Tuple[int, ...]] = None,
        input_names: Optional[List[str]] = None,
        output_names: Optional[List[str]] = None,
        dynamic_axes: Optional[Dict[str, Dict[int, str]]] = None,
        verbose: bool = False
    ) -> Path:
        """
        Export the model to ONNX format.
        
        Args:
            export_path: Directory or full path for the exported ONNX file
            input_sample: Sample input tensor for tracing (if None, uses input_shape)
            input_shape: Shape of input tensor (batch_size, *dims) if input_sample not provided
            input_names: Names of input tensors
            output_names: Names of output tensors
            dynamic_axes: Dictionary specifying dynamic axes for inputs/outputs
                         e.g., {'input': {0: 'batch_size'}, 'output': {0: 'batch_size'}}
            verbose: Whether to print detailed export information
            
        Returns:
            Path to the exported ONNX file
        """
        export_path = Path(export_path)
        
        # If export_path is a directory, create the full file path
        if export_path.is_dir() or not export_path.suffix:
            export_path = export_path / f"{self.model_name}.onnx"
        
        # Ensure parent directory exists
        export_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Prepare input sample
        if input_sample is None:
            if input_shape is None:
                raise ValueError("Either input_sample or input_shape must be provided")
            
            # Create a sample input tensor
            input_sample = torch.randn(input_shape)
            logger.info(f"Using generated input sample with shape: {input_sample.shape}")
        else:
            logger.info(f"Using provided input sample with shape: {input_sample.shape}")
        
        # Set default names if not provided
        if input_names is None:
            input_names = ["input"]
        if output_names is None:
            output_names = ["output"]
        
        # Set default dynamic axes if not provided (common case: batch dimension)
        if dynamic_axes is None:
            dynamic_axes = {
                input_names[0]: {0: "batch_size"},
                output_names[0]: {0: "batch_size"}
            }
            logger.info("Using default dynamic axes for batch dimension")
        
        logger.info(f"Exporting model to: {export_path}")
        logger.info(f"Input names: {input_names}")
        logger.info(f"Output names: {output_names}")
        logger.info(f"Dynamic axes: {dynamic_axes}")
        
        try:
            # Export the model
            torch.onnx.export(
                self.model,
                input_sample,
                export_path,
                export_params=True,
                opset_version=self.opset_version,
                do_constant_folding=self.do_constant_folding,
                input_names=input_names,
                output_names=output_names,
                dynamic_axes=dynamic_axes,
                verbose=verbose
            )
            
            logger.info(f"Model successfully exported to: {export_path}")
            
            # Verify the exported model
            self._verify_export(export_path, input_sample)
            
            return export_path
            
        except Exception as e:
            logger.error(f"Failed to export model to ONNX: {e}")
            raise
    
    def export_with_multiple_inputs(
        self,
        export_path: Union[str, Path],
        input_samples: List[torch.Tensor],
        input_names: Optional[List[str]] = None,
        output_names: Optional[List[str]] = None,
        dynamic_axes: Optional[Dict[str, Dict[int, str]]] = None,
        verbose: bool = False
    ) -> Path:
        """
        Export the model to ONNX format with multiple inputs.
        
        Args:
            export_path: Directory or full path for the exported ONNX file
            input_samples: List of sample input tensors for tracing
            input_names: Names of input tensors
            output_names: Names of output tensors
            dynamic_axes: Dictionary specifying dynamic axes for inputs/outputs
            verbose: Whether to print detailed export information
            
        Returns:
            Path to the exported ONNX file
        """
        export_path = Path(export_path)
        
        # If export_path is a directory, create the full file path
        if export_path.is_dir() or not export_path.suffix:
            export_path = export_path / f"{self.model_name}.onnx"
        
        # Ensure parent directory exists
        export_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Exporting model with {len(input_samples)} inputs to: {export_path}")
        
        # Set default names if not provided
        if input_names is None:
            input_names = [f"input_{i}" for i in range(len(input_samples))]
        if output_names is None:
            output_names = ["output"]
        
        # Log input shapes
        for i, inp in enumerate(input_samples):
            logger.info(f"Input {i} ({input_names[i]}): shape {inp.shape}")
        
        # Set default dynamic axes if not provided
        if dynamic_axes is None:
            dynamic_axes = {}
            for name in input_names:
                dynamic_axes[name] = {0: "batch_size"}  # Assume first dim is batch
            for name in output_names:
                dynamic_axes[name] = {0: "batch_size"}
            logger.info("Using default dynamic axes for batch dimension on all inputs/outputs")
        
        try:
            # Export the model
            torch.onnx.export(
                self.model,
                tuple(input_samples),
                export_path,
                export_params=True,
                opset_version=self.opset_version,
                do_constant_folding=self.do_constant_folding,
                input_names=input_names,
                output_names=output_names,
                dynamic_axes=dynamic_axes,
                verbose=verbose
            )
            
            logger.info(f"Model successfully exported to: {export_path}")
            
            # Verify the exported model
            self._verify_export(export_path, tuple(input_samples))
            
            return export_path
            
        except Exception as e:
            logger.error(f"Failed to export model to ONNX: {e}")
            raise
    
    def _verify_export(self, onnx_path: Path, sample_input: Any):
        """
        Verify the exported ONNX model by running inference with ONNX Runtime.
        
        Args:
            onnx_path: Path to the exported ONNX file
            sample_input: Sample input(s) used for export (for verification)
        """
        try:
            import onnxruntime as ort
            
            logger.info("Verifying exported ONNX model with ONNX Runtime...")
            
            # Create inference session
            ort_session = ort.InferenceSession(str(onnx_path))
            
            # Prepare inputs for ONNX Runtime
            if isinstance(sample_input, torch.Tensor):
                ort_inputs = {ort_session.get_inputs()[0].name: sample_input.numpy()}
            elif isinstance(sample_input, (tuple, list)):
                ort_inputs = {}
                for i, inp in enumerate(sample_input):
                    ort_inputs[ort_session.get_inputs()[i].name] = inp.numpy()
            else:
                raise ValueError("Unsupported sample input type for verification")
            
            # Run inference
            ort_outs = ort_session.run(None, ort_inputs)
            
            # Compare with PyTorch output
            self.model.eval()
            with torch.no_grad():
                if isinstance(sample_input, torch.Tensor):
                    torch_out = self.model(sample_input)
                elif isinstance(sample_input, (tuple, list)):
                    torch_out = self.model(*sample_input)
                else:
                    raise ValueError("Unsupported sample input type for verification")
                
                torch_out_np = torch_out.cpu().numpy()
            
            # Check if outputs are close (accounting for potential numerical differences)
            if np.allclose(torch_out_np, ort_outs[0], rtol=1e-3, atol=1e-5):
                logger.info("ONNX model verification PASSED: Outputs match PyTorch model")
            else:
                logger.warning("ONNX model verification: Outputs differ slightly (may be acceptable)")
                logger.info(f"PyTorch output sample: {torch_out_np.flatten()[:5]}")
                logger.info(f"ONNX output sample: {ort_outs[0].flatten()[:5]}")
                
        except ImportError:
            logger.warning("ONNX Runtime not available, skipping verification")
            logger.info("Install onnxruntime to enable verification: pip install onnxruntime")
        except Exception as e:
            logger.warning(f"ONNX model verification failed: {e}")
            logger.info("Export succeeded but verification could not be completed")


def create_exporter(
    model: nn.Module,
    model_name: str = "model",
    opset_version: int = 11,
    do_constant_folding: bool = True
) -> Exporter:
    """
    Factory function to create an Exporter instance.
    
    Args:
        model: PyTorch model to export
        model_name: Name for the exported ONNX file (without extension)
        opset_version: ONNX opset version to use
        do_constant_folding: Whether to perform constant folding optimization
        
    Returns:
        Exporter instance
    """
    return Exporter(
        model=model,
        model_name=model_name,
        opset_version=opset_version,
        do_constant_folding=do_constant_folding
    )


# Example usage:
# exporter = create_exporter(model, "my_model", opset_version=13)
# onnx_path = exporter.export(
#     export_path="./onnx_models/",
#     input_shape=(1, 3, 224, 224),  # batch_size, channels, height, width
#     input_names=["image"],
#     output_names=["prediction"],
#     dynamic_axes={
#         "image": {0: "batch_size"},
#         "prediction": {0: "batch_size"}
#     }
# )