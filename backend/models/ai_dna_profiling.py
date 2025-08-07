"""
AI Model DNA Profiling - Track model lineage and inheritance
"""

from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

class ModelInheritanceType(str, Enum):
    DIRECT = "direct"  # Direct parent-child relationship
    INFLUENCE = "influence"  # Model influenced by another
    FORK = "fork"  # Model forked from another
    MERGE = "merge"  # Model merged from multiple parents
    TRANSFER = "transfer"  # Knowledge transfer from another model

class BiasInheritanceType(str, Enum):
    INHERITED = "inherited"  # Directly inherited from parent
    AMPLIFIED = "amplified"  # Bias increased from parent
    REDUCED = "reduced"  # Bias decreased from parent
    NEW = "new"  # New bias introduced
    ELIMINATED = "eliminated"  # Bias removed from parent

class ModelDNAProfile(BaseModel):
    model_id: str
    dna_signature: str  # Unique DNA signature
    parent_models: List[str] = []
    child_models: List[str] = []
    inheritance_type: ModelInheritanceType
    creation_date: datetime
    version: str
    algorithm_family: str
    training_data_sources: List[Dict[str, Any]]
    bias_inheritance: List[Dict[str, Any]]
    performance_characteristics: Dict[str, Any]
    ethical_framework: Dict[str, Any]
    risk_profile: Dict[str, Any]

class BiasInheritancePattern(BaseModel):
    bias_type: str
    inheritance_type: BiasInheritanceType
    parent_value: float
    current_value: float
    change_magnitude: float
    change_direction: str  # "increase", "decrease", "same"
    explanation: str

class ModelLineageNode(BaseModel):
    model_id: str
    generation: int
    parents: List[str]
    children: List[str]
    dna_signature: str
    creation_date: datetime
    bias_score: float
    performance_score: float
    risk_level: str

class ModelEvolution(BaseModel):
    model_id: str
    evolution_path: List[ModelLineageNode]
    bias_evolution: List[BiasInheritancePattern]
    performance_trend: List[Dict[str, Any]]
    risk_evolution: List[Dict[str, Any]]

def generate_dna_signature(model_data: Dict[str, Any]) -> str:
    """Generate unique DNA signature for a model"""
    import hashlib
    import json
    
    # Create a unique signature based on model characteristics
    signature_data = {
        "algorithm": model_data.get("algorithm", ""),
        "architecture": model_data.get("architecture", ""),
        "training_data_hash": model_data.get("training_data_hash", ""),
        "hyperparameters": model_data.get("hyperparameters", {}),
        "bias_characteristics": model_data.get("bias_characteristics", {}),
        "performance_metrics": model_data.get("performance_metrics", {})
    }
    
    signature_string = json.dumps(signature_data, sort_keys=True)
    return hashlib.sha256(signature_string.encode()).hexdigest()[:16]

def analyze_bias_inheritance(parent_model: Dict[str, Any], child_model: Dict[str, Any]) -> List[BiasInheritancePattern]:
    """Analyze how bias is inherited from parent to child model"""
    inheritance_patterns = []
    
    parent_biases = parent_model.get("bias_characteristics", {})
    child_biases = child_model.get("bias_characteristics", {})
    
    for bias_type in set(parent_biases.keys()) | set(child_biases.keys()):
        parent_value = parent_biases.get(bias_type, 0.0)
        child_value = child_biases.get(bias_type, 0.0)
        
        if bias_type in parent_biases and bias_type in child_biases:
            if child_value > parent_value:
                inheritance_type = BiasInheritanceType.AMPLIFIED
                change_direction = "increase"
            elif child_value < parent_value:
                inheritance_type = BiasInheritanceType.REDUCED
                change_direction = "decrease"
            else:
                inheritance_type = BiasInheritanceType.INHERITED
                change_direction = "same"
        elif bias_type in parent_biases:
            inheritance_type = BiasInheritanceType.ELIMINATED
            change_direction = "decrease"
        else:
            inheritance_type = BiasInheritanceType.NEW
            change_direction = "increase"
        
        change_magnitude = abs(child_value - parent_value)
        
        inheritance_patterns.append(BiasInheritancePattern(
            bias_type=bias_type,
            inheritance_type=inheritance_type,
            parent_value=parent_value,
            current_value=child_value,
            change_magnitude=change_magnitude,
            change_direction=change_direction,
            explanation=f"Bias {bias_type} {change_direction} from {parent_value:.3f} to {child_value:.3f}"
        ))
    
    return inheritance_patterns

def create_model_lineage_tree(models: List[Dict[str, Any]]) -> List[ModelLineageNode]:
    """Create a lineage tree from model data"""
    lineage_nodes = []
    
    for model in models:
        node = ModelLineageNode(
            model_id=model["model_id"],
            generation=model.get("generation", 0),
            parents=model.get("parent_models", []),
            children=model.get("child_models", []),
            dna_signature=model.get("dna_signature", ""),
            creation_date=datetime.fromisoformat(model.get("creation_date", datetime.now().isoformat())),
            bias_score=model.get("bias_score", 0.0),
            performance_score=model.get("performance_score", 0.0),
            risk_level=model.get("risk_level", "UNKNOWN")
        )
        lineage_nodes.append(node)
    
    return lineage_nodes

def analyze_model_evolution(model_id: str, lineage_data: List[Dict[str, Any]]) -> ModelEvolution:
    """Analyze the evolution of a specific model through its lineage"""
    # Find the model and its ancestors
    model_lineage = []
    current_model = None
    
    for model in lineage_data:
        if model["model_id"] == model_id:
            current_model = model
            break
    
    if not current_model:
        raise ValueError(f"Model {model_id} not found in lineage data")
    
    # Build evolution path
    evolution_path = []
    bias_evolution = []
    performance_trend = []
    risk_evolution = []
    
    # Traverse up the lineage
    current = current_model
    generation = 0
    
    while current:
        node = ModelLineageNode(
            model_id=current["model_id"],
            generation=generation,
            parents=current.get("parent_models", []),
            children=current.get("child_models", []),
            dna_signature=current.get("dna_signature", ""),
            creation_date=datetime.fromisoformat(current.get("creation_date", datetime.now().isoformat())),
            bias_score=current.get("bias_score", 0.0),
            performance_score=current.get("performance_score", 0.0),
            risk_level=current.get("risk_level", "UNKNOWN")
        )
        evolution_path.append(node)
        
        # Analyze bias evolution if there's a parent
        if current.get("parent_models"):
            parent = next((m for m in lineage_data if m["model_id"] == current["parent_models"][0]), None)
            if parent:
                bias_patterns = analyze_bias_inheritance(parent, current)
                bias_evolution.extend(bias_patterns)
        
        # Track performance and risk
        performance_trend.append({
            "model_id": current["model_id"],
            "generation": generation,
            "performance_score": current.get("performance_score", 0.0),
            "date": current.get("creation_date", datetime.now().isoformat())
        })
        
        risk_evolution.append({
            "model_id": current["model_id"],
            "generation": generation,
            "risk_level": current.get("risk_level", "UNKNOWN"),
            "bias_score": current.get("bias_score", 0.0),
            "date": current.get("creation_date", datetime.now().isoformat())
        })
        
        # Move to parent
        if current.get("parent_models"):
            current = next((m for m in lineage_data if m["model_id"] == current["parent_models"][0]), None)
        else:
            current = None
        
        generation += 1
    
    return ModelEvolution(
        model_id=model_id,
        evolution_path=evolution_path,
        bias_evolution=bias_evolution,
        performance_trend=performance_trend,
        risk_evolution=risk_evolution
    ) 