"""
Marketplace Service

Handles model publishing, searching, and reviews for the Model Marketplace.
"""

import logging
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import uuid
from sqlalchemy import text
import sys
from pathlib import Path

# Add parent directory to path to ensure imports work
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from database.connection import db_manager

logger = logging.getLogger(__name__)

@dataclass
class ModelTag:
    """Tag for categorizing models"""
    name: str
    category: str  # e.g., "task", "framework", "language"

@dataclass
class ModelReview:
    """User review for a model"""
    review_id: str
    model_id: str
    user_id: str
    rating: int
    comment: str
    created_at: str

@dataclass
class MarketplaceModel:
    """Model listed in the marketplace"""
    model_id: str
    name: str
    description: str
    author: str
    version: str
    framework: str
    task: str
    tags: List[ModelTag]
    bias_card: Dict[str, Any]  # Summary of bias metrics
    performance_metrics: Dict[str, float]
    reviews: List[ModelReview] = field(default_factory=list)
    download_count: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    @property
    def average_rating(self) -> float:
        if not self.reviews:
            return 0.0
        return sum(r.rating for r in self.reviews) / len(self.reviews)

class MarketplaceService:
    """
    Service for managing the Model Marketplace.
    """
    
    def __init__(self):
        pass

    def _map_db_row_to_model(self, row: Any) -> MarketplaceModel:
        """Helper to map a database row to a MarketplaceModel object"""
        metadata = json.loads(row.metadata) if isinstance(row.metadata, str) else (row.metadata or {})
        tags_json = json.loads(row.tags) if isinstance(row.tags, str) else (row.tags or [])
        
        # Parse tags
        tags = []
        for t in tags_json:
            if isinstance(t, dict):
                tags.append(ModelTag(t.get("name", ""), t.get("category", "general")))
            elif isinstance(t, str):
                tags.append(ModelTag(t, "general"))
                
        # Default bias card if not present
        default_bias_card = {
            "overall_score": 0.85,
            "metrics": {
                "gender_bias": 0.1,
                "racial_bias": 0.1
            }
        }
        
        return MarketplaceModel(
            model_id=row.id,
            name=row.name,
            description=row.description or "",
            author=row.created_by or "Unknown",
            version=row.version or "1.0.0",
            framework=metadata.get("framework", "Unknown"),
            task=row.model_type or "Unknown",
            tags=tags,
            bias_card=metadata.get("bias_card", default_bias_card),
            performance_metrics=metadata.get("performance_metrics", {}),
            reviews=[], # No reviews table yet
            download_count=metadata.get("download_count", 0),
            created_at=row.upload_date.isoformat() if row.upload_date else datetime.now().isoformat(),
            updated_at=row.updated_at.isoformat() if row.updated_at else datetime.now().isoformat()
        )

    async def list_models(
        self, 
        search_query: Optional[str] = None, 
        framework: Optional[str] = None,
        task: Optional[str] = None,
        min_rating: Optional[float] = None
    ) -> List[MarketplaceModel]:
        """
        List models with filtering options.
        """
        query_parts = ["SELECT * FROM models WHERE status = 'active'"]
        params = {}
        
        if search_query:
            query_parts.append("AND (lower(name) LIKE :query OR lower(description) LIKE :query)")
            params["query"] = f"%{search_query.lower()}%"
            
        if framework:
            # This is a bit tricky with JSONB in SQLite/Postgres abstraction, 
            # but for now we'll filter in Python if needed or use simple text match on metadata
            query_parts.append("AND metadata LIKE :framework")
            params["framework"] = f"%{framework}%"
            
        if task:
            query_parts.append("AND model_type = :task")
            params["task"] = task
            
        query_str = " ".join(query_parts)
        
        results = []
        with db_manager.get_session() as session:
            rows = session.execute(text(query_str), params).fetchall()
            for row in rows:
                model = self._map_db_row_to_model(row)
                
                # Post-filtering for rating since we don't have it in DB query easily yet
                if min_rating and model.average_rating < min_rating:
                    continue
                    
                results.append(model)
                
        return results

    async def get_model(self, model_id: str) -> Optional[MarketplaceModel]:
        """
        Get a specific model by ID.
        """
        with db_manager.get_session() as session:
            query = text("SELECT * FROM models WHERE id = :id")
            row = session.execute(query, {"id": model_id}).fetchone()
            
            if row:
                return self._map_db_row_to_model(row)
            return None

    async def publish_model(self, model_data: Dict[str, Any]) -> MarketplaceModel:
        """
        Publish a new model to the marketplace.
        """
        model_id = str(uuid.uuid4())
        now = datetime.now()
        
        # Prepare metadata
        metadata = {
            "framework": model_data.get("framework"),
            "bias_card": model_data.get("bias_card", {}),
            "performance_metrics": model_data.get("performance_metrics", {}),
            "download_count": 0
        }
        
        # Prepare tags
        tags_data = model_data.get("tags", [])
        # Ensure tags are stored as list of dicts or strings
        
        with db_manager.get_session() as session:
            insert_query = text("""
                INSERT INTO models (
                    id, name, description, model_type, version, status,
                    tags, metadata, created_by, upload_date, updated_at
                ) VALUES (
                    :id, :name, :description, :model_type, :version, 'active',
                    :tags, :metadata, :created_by, :upload_date, :updated_at
                )
            """)
            
            session.execute(insert_query, {
                "id": model_id,
                "name": model_data["name"],
                "description": model_data["description"],
                "model_type": model_data["task"], # Mapping task to model_type
                "version": model_data["version"],
                "tags": json.dumps(tags_data),
                "metadata": json.dumps(metadata),
                "created_by": model_data.get("author", "Unknown"),
                "upload_date": now,
                "updated_at": now
            })
            session.commit()
            
        # Return the created model object
        return await self.get_model(model_id)

    async def add_review(self, model_id: str, review_data: Dict[str, Any]) -> ModelReview:
        """
        Add a review to a model.
        """
        # Since we don't have a reviews table, we'll just return a mock review for now
        # In a real implementation, we would insert into a reviews table
        
        # Verify model exists
        model = await self.get_model(model_id)
        if not model:
            raise ValueError(f"Model {model_id} not found")
            
        review = ModelReview(
            review_id=str(uuid.uuid4()),
            model_id=model_id,
            user_id=review_data["user_id"],
            rating=review_data["rating"],
            comment=review_data["comment"],
            created_at=datetime.now().isoformat()
        )
        
        # We can't persist it without a table, so we just log it
        logger.info(f"Review added for model {model_id}: {review}")
        
        return review

# Singleton instance
marketplace_service = MarketplaceService()
