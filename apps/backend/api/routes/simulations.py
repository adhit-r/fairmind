"""
Simulation API Routes
Handles ML model execution and simulation management
"""

from fastapi import APIRouter, HTTPException, Body, Query, Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import json
from pydantic import BaseModel

# Import services
from ..services.simulation_service import simulation_service, SimulationConfig
from ..services.dataset_service import dataset_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/simulations", tags=["simulations"])

# Pydantic Models
class SimulationRequest(BaseModel):
    """Request model for running simulation"""
    dataset_id: str
    model_type: str  # 'classification' or 'regression'
    algorithm: str   # 'random_forest', 'logistic_regression', 'linear_regression'
    target_column: str
    feature_columns: List[str]
    protected_attributes: List[str]
    test_size: float = 0.2
    random_state: int = 42
    hyperparameters: Optional[Dict[str, Any]] = None

class SimulationResponse(BaseModel):
    """Response model for simulation operations"""
    success: bool
    simulation_id: Optional[str] = None
    results: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    error: Optional[str] = None

class SimulationListResponse(BaseModel):
    """Response model for simulation listing"""
    success: bool
    simulations: List[Dict[str, Any]]
    total: int

@router.post("/run", response_model=SimulationResponse)
async def run_simulation(request: SimulationRequest):
    """
    Run ML simulation on dataset
    
    This endpoint:
    - Validates simulation configuration
    - Executes ML model training
    - Calculates performance and fairness metrics
    - Returns simulation results
    """
    try:
        logger.info(f"Starting simulation for dataset: {request.dataset_id}")
        
        # Validate dataset exists and get file path
        # For now, we'll use a mock path - in production this would come from database
        dataset_path = f"sample_datasets/sample_income_data.csv"
        
        # Create simulation config
        config = SimulationConfig(
            model_type=request.model_type,
            algorithm=request.algorithm,
            target_column=request.target_column,
            feature_columns=request.feature_columns,
            protected_attributes=request.protected_attributes,
            test_size=request.test_size,
            random_state=request.random_state,
            hyperparameters=request.hyperparameters
        )
        
        # Run simulation
        result = await simulation_service.run_simulation(
            dataset_path=dataset_path,
            config=config
        )
        
        if result["success"]:
            logger.info(f"Simulation completed: {result['simulation_id']}")
            return SimulationResponse(
                success=True,
                simulation_id=result["simulation_id"],
                results=result["results"],
                message=result["message"]
            )
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Simulation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=SimulationListResponse)
async def list_simulations(
    limit: int = Query(10, ge=1, le=100, description="Number of simulations to return"),
    status: Optional[str] = Query(None, description="Filter by status")
):
    """
    List recent simulations
    
    This endpoint:
    - Returns paginated list of simulations
    - Supports filtering by status
    - Includes basic metadata
    """
    try:
        simulations = await simulation_service.list_simulations(limit=limit)
        
        # Apply status filter if specified
        if status:
            simulations = [s for s in simulations if s.get("status") == status]
        
        return SimulationListResponse(
            success=True,
            simulations=simulations,
            total=len(simulations)
        )
        
    except Exception as e:
        logger.error(f"Failed to list simulations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{simulation_id}", response_model=SimulationResponse)
async def get_simulation(simulation_id: str = Path(..., description="Simulation ID")):
    """
    Get simulation details and results
    
    This endpoint:
    - Returns complete simulation information
    - Includes performance and fairness metrics
    - Shows configuration and execution details
    """
    try:
        results = await simulation_service.get_simulation_status(simulation_id)
        
        if results.get("status") == "not_found":
            raise HTTPException(status_code=404, detail="Simulation not found")
        
        if results.get("status") == "error":
            raise HTTPException(status_code=500, detail=results.get("error", "Unknown error"))
        
        return SimulationResponse(
            success=True,
            simulation_id=simulation_id,
            results=results,
            message="Simulation retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get simulation {simulation_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{simulation_id}", response_model=SimulationResponse)
async def delete_simulation(simulation_id: str = Path(..., description="Simulation ID")):
    """
    Delete simulation and associated files
    
    This endpoint:
    - Removes simulation results
    - Deletes trained model files
    - Cleans up storage
    """
    try:
        success = await simulation_service.delete_simulation(simulation_id)
        
        if success:
            return SimulationResponse(
                success=True,
                message=f"Simulation {simulation_id} deleted successfully"
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to delete simulation")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete simulation {simulation_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{simulation_id}/rerun", response_model=SimulationResponse)
async def rerun_simulation(
    simulation_id: str = Path(..., description="Simulation ID"),
    request: SimulationRequest = Body(...)
):
    """
    Rerun simulation with new configuration
    
    This endpoint:
    - Loads original simulation configuration
    - Allows parameter modifications
    - Executes new simulation
    - Returns updated results
    """
    try:
        logger.info(f"Rerunning simulation: {simulation_id}")
        
        # Get original simulation to extract dataset path
        original_results = await simulation_service.get_simulation_status(simulation_id)
        if original_results.get("status") == "not_found":
            raise HTTPException(status_code=404, detail="Original simulation not found")
        
        # Use dataset path from original simulation
        dataset_path = f"sample_datasets/sample_income_data.csv"  # Mock path
        
        # Create new config
        config = SimulationConfig(
            model_type=request.model_type,
            algorithm=request.algorithm,
            target_column=request.target_column,
            feature_columns=request.feature_columns,
            protected_attributes=request.protected_attributes,
            test_size=request.test_size,
            random_state=request.random_state,
            hyperparameters=request.hyperparameters
        )
        
        # Run new simulation
        result = await simulation_service.run_simulation(
            dataset_path=dataset_path,
            config=config
        )
        
        if result["success"]:
            logger.info(f"Simulation rerun completed: {result['simulation_id']}")
            return SimulationResponse(
                success=True,
                simulation_id=result["simulation_id"],
                results=result["results"],
                message="Simulation rerun completed successfully"
            )
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Simulation rerun failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{simulation_id}/status")
async def get_simulation_status(simulation_id: str = Path(..., description="Simulation ID")):
    """
    Get simulation execution status
    
    This endpoint:
    - Returns current simulation status
    - Shows execution progress
    - Includes timing information
    """
    try:
        results = await simulation_service.get_simulation_status(simulation_id)
        
        if results.get("status") == "not_found":
            raise HTTPException(status_code=404, detail="Simulation not found")
        
        return {
            "success": True,
            "simulation_id": simulation_id,
            "status": results.get("status"),
            "execution_time_ms": results.get("execution_time_ms"),
            "created_at": results.get("created_at"),
            "error_message": results.get("error_message")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get simulation status {simulation_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/algorithms/available")
async def get_available_algorithms():
    """
    Get available ML algorithms and their capabilities
    
    This endpoint:
    - Lists supported algorithms
    - Shows model types (classification/regression)
    - Includes default hyperparameters
    """
    try:
        algorithms = {
            "classification": {
                "random_forest": {
                    "description": "Random Forest Classifier",
                    "hyperparameters": {
                        "n_estimators": {"type": "int", "default": 100, "min": 10, "max": 1000},
                        "random_state": {"type": "int", "default": 42}
                    }
                },
                "logistic_regression": {
                    "description": "Logistic Regression",
                    "hyperparameters": {
                        "random_state": {"type": "int", "default": 42},
                        "max_iter": {"type": "int", "default": 1000, "min": 100, "max": 10000}
                    }
                }
            },
            "regression": {
                "random_forest": {
                    "description": "Random Forest Regressor",
                    "hyperparameters": {
                        "n_estimators": {"type": "int", "default": 100, "min": 10, "max": 1000},
                        "random_state": {"type": "int", "default": 42}
                    }
                },
                "linear_regression": {
                    "description": "Linear Regression",
                    "hyperparameters": {}
                }
            }
        }
        
        return {
            "success": True,
            "algorithms": algorithms
        }
        
    except Exception as e:
        logger.error(f"Failed to get available algorithms: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/validate-config")
async def validate_simulation_config(request: SimulationRequest):
    """
    Validate simulation configuration without running
    
    This endpoint:
    - Checks configuration validity
    - Validates against dataset schema
    - Returns validation results
    """
    try:
        # Mock dataset path for validation
        dataset_path = f"sample_datasets/sample_income_data.csv"
        
        # Load dataset to validate against
        df = await simulation_service._load_dataset(dataset_path)
        
        # Validate configuration
        await simulation_service._validate_config(df, SimulationConfig(
            model_type=request.model_type,
            algorithm=request.algorithm,
            target_column=request.target_column,
            feature_columns=request.feature_columns,
            protected_attributes=request.protected_attributes,
            test_size=request.test_size,
            random_state=request.random_state,
            hyperparameters=request.hyperparameters
        ))
        
        return {
            "success": True,
            "message": "Configuration validation passed",
            "validation": {
                "dataset_shape": df.shape,
                "available_columns": list(df.columns),
                "target_column": request.target_column,
                "feature_columns": request.feature_columns,
                "protected_attributes": request.protected_attributes,
                "model_type": request.model_type,
                "algorithm": request.algorithm
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "validation": {
                "target_column": request.target_column,
                "feature_columns": request.feature_columns,
                "protected_attributes": request.protected_attributes,
                "model_type": request.model_type,
                "algorithm": request.algorithm
            }
        }
