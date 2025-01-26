"""
Configuration for Ollama integration optimized for M3 silicon chip.
Includes Metal framework acceleration and resource monitoring.
"""

import platform
import psutil
import GPUtil
from typing import Dict, Any
import logging
import os
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OllamaConfig:
    def __init__(self):
        self.base_url = "http://localhost:11434"
        self.is_m3 = self._check_m3_chip()
        self.metal_enabled = self._check_metal_support()
        self.model_path = Path.home() / ".ollama" / "models"
        
    def _check_m3_chip(self) -> bool:
        """Check if running on M3 chip."""
        try:
            return platform.processor() == 'arm' and 'M3' in platform.machine()
        except Exception as e:
            logger.warning(f"Failed to detect M3 chip: {e}")
            return False

    def _check_metal_support(self) -> bool:
        """Check Metal framework support."""
        try:
            return platform.system() == 'Darwin' and self.is_m3
        except Exception as e:
            logger.warning(f"Failed to detect Metal support: {e}")
            return False

    def get_optimal_config(self) -> Dict[str, Any]:
        """Get optimal configuration for M3 chip."""
        config = {
            "use_metal": self.metal_enabled,
            "threads": psutil.cpu_count(logical=False),
            "batch_size": 512 if self.is_m3 else 256,
            "context_size": 4096,
            "gpu_layers": -1 if self.metal_enabled else 0
        }
        
        if self.metal_enabled:
            config.update({
                "metal_device": 0,  # Use primary GPU
                "metal_memory": int(psutil.virtual_memory().available * 0.7)  # 70% of available RAM
            })
            
        return config

    def get_resource_usage(self) -> Dict[str, Any]:
        """Monitor system resource usage."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            usage = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used": memory.used,
                "memory_available": memory.available
            }
            
            if self.metal_enabled:
                try:
                    gpus = GPUtil.getGPUs()
                    if gpus:
                        gpu = gpus[0]  # Primary GPU
                        usage.update({
                            "gpu_load": gpu.load * 100,
                            "gpu_memory_used": gpu.memoryUsed,
                            "gpu_memory_total": gpu.memoryTotal
                        })
                except Exception as e:
                    logger.warning(f"Failed to get GPU metrics: {e}")
            
            return usage
        except Exception as e:
            logger.error(f"Failed to get resource usage: {e}")
            return {}

    def optimize_model_params(self, model_name: str) -> Dict[str, Any]:
        """Optimize model parameters for M3 chip."""
        base_params = {
            "num_ctx": 4096,
            "num_batch": 512,
            "num_thread": psutil.cpu_count(logical=False),
            "rope_frequency_base": 10000.0,
            "rope_frequency_scale": 1.0,
            "num_gpu": 1 if self.metal_enabled else 0
        }
        
        # Model-specific optimizations
        if "medical" in model_name.lower():
            base_params.update({
                "num_ctx": 8192,  # Larger context for medical texts
                "rope_frequency_scale": 0.5  # Better for medical terminology
            })
            
        if self.metal_enabled:
            base_params.update({
                "metal_layers": -1,  # Use Metal for all layers
                "metal_throughput": True,
                "metal_memory_efficient": True
            })
            
        return base_params

    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """Get model information and status."""
        model_path = self.model_path / model_name
        
        if not model_path.exists():
            return {"status": "not_found"}
            
        try:
            stats = model_path.stat()
            return {
                "status": "loaded",
                "size_bytes": stats.st_size,
                "last_modified": stats.st_mtime,
                "optimized_for_m3": self.is_m3,
                "metal_acceleration": self.metal_enabled,
                "parameters": self.optimize_model_params(model_name)
            }
        except Exception as e:
            logger.error(f"Failed to get model info: {e}")
            return {"status": "error", "message": str(e)}
