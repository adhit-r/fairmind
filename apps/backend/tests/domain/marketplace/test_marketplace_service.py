import pytest
from datetime import datetime
from apps.backend.domain.marketplace.services.marketplace_service import marketplace_service, MarketplaceModel, ModelReview

@pytest.mark.asyncio
async def test_publish_model():
    model_data = {
        "name": "Test Model",
        "description": "A test model",
        "author": "Tester",
        "version": "1.0.0",
        "framework": "PyTorch",
        "task": "Classification",
        "tags": [{"name": "test", "category": "general"}],
        "bias_card": {"overall_score": 0.9},
        "performance_metrics": {"accuracy": 0.95}
    }
    
    model = await marketplace_service.publish_model(model_data)
    
    assert model.name == "Test Model"
    assert model.model_id is not None
    assert len(model.tags) == 1
    assert model.tags[0].name == "test"

@pytest.mark.asyncio
async def test_list_models():
    # Ensure we have at least one model (from previous test or mock data)
    models = await marketplace_service.list_models()
    assert len(models) > 0
    
    # Test filtering
    filtered = await marketplace_service.list_models(search_query="GPT-2")
    assert len(filtered) > 0
    assert "GPT-2" in filtered[0].name

@pytest.mark.asyncio
async def test_add_review():
    # Get an existing model ID
    models = await marketplace_service.list_models()
    model_id = models[0].model_id
    
    review_data = {
        "user_id": "reviewer1",
        "rating": 5,
        "comment": "Excellent!"
    }
    
    review = await marketplace_service.add_review(model_id, review_data)
    
    assert review.model_id == model_id
    assert review.rating == 5
    assert review.comment == "Excellent!"
    
    # Verify review is attached to model
    updated_model = await marketplace_service.get_model(model_id)
    assert len(updated_model.reviews) > 0
    assert updated_model.reviews[-1].comment == "Excellent!"
