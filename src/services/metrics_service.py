import asyncio
import logging
import psutil
import time
from dataclasses import dataclass
from typing import Optional

from models.encryption import M3Metrics, MetricsResponse
from core.config import Settings

logger = logging.getLogger("iqhis.metrics")

@dataclass
class MetricsData:
    encryption_operations: int
    key_rotations: int
    error_count: int
    m3_metrics: Optional[M3Metrics]

class MetricsService:
    def __init__(self):
        self.settings = Settings()
        self.encryption_operations = 0
        self.key_rotations = 0
        self.error_count = 0
        self.start_time = time.time()

        # Start background metrics collection
        asyncio.create_task(self._collect_metrics())

    async def _collect_metrics(self):
        """Background task to collect system metrics."""
        while True:
            try:
                # Collect CPU metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                
                # Collect memory metrics
                memory = psutil.virtual_memory()
                memory_percent = memory.percent

                # Collect GPU metrics if available
                gpu_percent = self._get_gpu_utilization()

                # Update M3 metrics
                self.m3_metrics = M3Metrics(
                    cpu_utilization=cpu_percent,
                    memory_usage=memory_percent,
                    gpu_utilization=gpu_percent
                )

                # Wait before next collection
                await asyncio.sleep(self.settings.METRICS_COLLECTION_INTERVAL)

            except Exception as e:
                logger.error(f"Metrics collection error: {str(e)}")
                self.error_count += 1
                await asyncio.sleep(5)  # Wait before retry

    def _get_gpu_utilization(self) -> float:
        """Get GPU utilization percentage."""
        try:
            # TODO: Implement actual GPU metrics collection
            # This is a placeholder for Sprint 0
            return 50.0
        except Exception as e:
            logger.warning(f"GPU metrics collection error: {str(e)}")
            return 0.0

    def increment_encryption_operations(self):
        """Increment the count of encryption operations."""
        self.encryption_operations += 1

    def increment_key_rotations(self):
        """Increment the count of key rotations."""
        self.key_rotations += 1

    def increment_errors(self):
        """Increment the error count."""
        self.error_count += 1

    async def get_metrics(self) -> MetricsData:
        """Get current system metrics."""
        try:
            return MetricsData(
                encryption_operations=self.encryption_operations,
                key_rotations=self.key_rotations,
                error_count=self.error_count,
                m3_metrics=self.m3_metrics
            )
        except Exception as e:
            logger.error(f"Error retrieving metrics: {str(e)}")
            raise 