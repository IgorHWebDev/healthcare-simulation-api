"""
HPC Orchestrator for managing quantum circuits and parallel processing in the IQHIS system.
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional

import ray
import dask
import dask_cuda
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hpc_orchestrator")

class CircuitConfig(BaseModel):
    """Configuration for quantum circuit execution."""
    num_qubits: int = Field(default=4, ge=1, le=32)
    shots: int = Field(default=1000, ge=100, le=10000)
    optimization_level: int = Field(default=3, ge=0, le=3)
    backend: str = Field(default="aer_simulator")

class HPCOrchestrator:
    """Manages HPC resources and quantum circuit execution."""
    
    def __init__(self, max_parallel_circuits: int = 1000):
        self.max_parallel_circuits = max_parallel_circuits
        self.active_circuits: Dict[str, asyncio.Task] = {}
        
        # Initialize Ray for distributed computing
        ray.init(ignore_reinit_error=True)
        
        # Initialize Dask with CUDA
        self.cluster = dask_cuda.LocalCUDACluster(
            n_workers=4,
            threads_per_worker=1
        )
        self.client = dask.distributed.Client(self.cluster)
        
        logger.info("HPC Orchestrator initialized with GPU support")
    
    async def start_circuit(self, circuit_id: str, config: CircuitConfig) -> str:
        """Start a new quantum circuit execution."""
        if len(self.active_circuits) >= self.max_parallel_circuits:
            raise HTTPException(
                status_code=429,
                detail="Maximum number of parallel circuits reached"
            )
        
        task = asyncio.create_task(
            self._run_circuit(circuit_id, config)
        )
        self.active_circuits[circuit_id] = task
        
        logger.info(f"Started circuit {circuit_id} with {config.num_qubits} qubits")
        return circuit_id
    
    @ray.remote(num_gpus=1)
    def _run_circuit(self, circuit_id: str, config: CircuitConfig) -> Dict:
        """Execute a quantum circuit with the given configuration."""
        try:
            # Import Qiskit here to ensure it's only loaded in the Ray worker
            from qiskit import QuantumCircuit, Aer, execute
            
            # Create and configure the circuit
            qc = QuantumCircuit(config.num_qubits, config.num_qubits)
            for qubit in range(config.num_qubits):
                qc.h(qubit)
            qc.measure_all()
            
            # Execute the circuit
            backend = Aer.get_backend(config.backend)
            job = execute(
                qc,
                backend,
                shots=config.shots,
                optimization_level=config.optimization_level
            )
            result = job.result()
            
            return {
                "circuit_id": circuit_id,
                "status": "completed",
                "counts": result.get_counts(qc),
                "metadata": result.to_dict()
            }
            
        except Exception as e:
            logger.error(f"Error executing circuit {circuit_id}: {str(e)}")
            return {
                "circuit_id": circuit_id,
                "status": "failed",
                "error": str(e)
            }
    
    async def get_circuit_status(self, circuit_id: str) -> Dict:
        """Get the status of a running circuit."""
        if circuit_id not in self.active_circuits:
            raise HTTPException(
                status_code=404,
                detail=f"Circuit {circuit_id} not found"
            )
        
        task = self.active_circuits[circuit_id]
        if task.done():
            try:
                result = await task
                return result
            except Exception as e:
                return {
                    "circuit_id": circuit_id,
                    "status": "failed",
                    "error": str(e)
                }
        
        return {
            "circuit_id": circuit_id,
            "status": "running"
        }
    
    async def stop_circuit(self, circuit_id: str) -> Dict:
        """Stop a running circuit."""
        if circuit_id not in self.active_circuits:
            raise HTTPException(
                status_code=404,
                detail=f"Circuit {circuit_id} not found"
            )
        
        task = self.active_circuits[circuit_id]
        task.cancel()
        
        try:
            await task
        except asyncio.CancelledError:
            pass
        
        del self.active_circuits[circuit_id]
        return {
            "circuit_id": circuit_id,
            "status": "stopped"
        }
    
    def get_metrics(self) -> Dict:
        """Get current HPC metrics."""
        return {
            "active_circuits": len(self.active_circuits),
            "gpu_memory_used": self.client.run(dask_cuda.utils.get_gpu_memory_used),
            "worker_count": len(self.client.scheduler_info()["workers"])
        }
    
    async def cleanup(self):
        """Cleanup resources on shutdown."""
        for circuit_id in list(self.active_circuits.keys()):
            await self.stop_circuit(circuit_id)
        
        self.client.close()
        self.cluster.close()
        ray.shutdown()

# Create FastAPI application
app = FastAPI(title="HPC Orchestrator API")
orchestrator: Optional[HPCOrchestrator] = None

@app.on_event("startup")
async def startup_event():
    """Initialize the HPC orchestrator on startup."""
    global orchestrator
    orchestrator = HPCOrchestrator()

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on shutdown."""
    global orchestrator
    if orchestrator:
        await orchestrator.cleanup()

@app.post("/circuits/")
async def create_circuit(config: CircuitConfig):
    """Create and start a new quantum circuit."""
    circuit_id = f"circuit_{len(orchestrator.active_circuits) + 1}"
    return await orchestrator.start_circuit(circuit_id, config)

@app.get("/circuits/{circuit_id}")
async def get_circuit(circuit_id: str):
    """Get the status of a specific circuit."""
    return await orchestrator.get_circuit_status(circuit_id)

@app.delete("/circuits/{circuit_id}")
async def delete_circuit(circuit_id: str):
    """Stop and remove a specific circuit."""
    return await orchestrator.stop_circuit(circuit_id)

@app.get("/metrics")
async def get_metrics():
    """Get current HPC metrics."""
    return orchestrator.get_metrics()

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 