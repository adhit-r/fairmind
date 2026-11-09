"""
LLM-as-Judge API Routes
Exposes LLM-as-Judge bias evaluation endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from config.auth import TokenData, get_current_active_user
from database.connection import get_db
from api.routes.ai_governance import (
    CLOSED_RISK_STATUSES,
    _authenticated_actor,
    _caller_org,
    _enforce_org_scope,
    _ensure_tables,
    _require_system_access,
    _risk_score,
)
from api.routes import llm
from src.application.services import bias_analysis_store as store
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import json
import logging
import uuid
from datetime import datetime

from ..services.llm_as_judge_service import (
    LLMAsJudgeService,
    JudgeModel,
    BiasCategory,
    JudgeEvaluationResult
)
from src.application.services.llm_runtime import grok_cli

logger = logging.getLogger(__name__)
# Stateless: scores the text in the request. It spends the platform's judge-model
# API budget, so the caller must be signed in.
router = APIRouter(
    prefix="/bias/llm-judge",
    tags=["llm-judge"],
    dependencies=[Depends(get_current_active_user), Depends(_enforce_org_scope)],
)

# Initialize service
llm_judge_service = LLMAsJudgeService()

JUDGE_LABELS = {
    JudgeModel.GPT_6_ASTRA: "GPT-6 Astra (OpenAI)",
    JudgeModel.GPT_6_1_SOL: "GPT-6.1 Sol (OpenAI)",
    JudgeModel.CLAUDE_OPUS_5_5: "Claude Opus 5.5 (Anthropic)",
    JudgeModel.CLAUDE_SONNET_5_5: "Claude Sonnet 5.5 (Anthropic)",
    JudgeModel.GEMINI_4_ARGON: "Gemini 4 Argon (Google)",
    JudgeModel.GEMINI_3_8_FLASH: "Gemini 3.8 Flash (Google)",
    JudgeModel.GROK_4_7: "Grok 4.7 (Grok CLI, local)",
    JudgeModel.GROK_4_6: "Grok 4.6 (Grok CLI, local)",
}
GROK_CLI_OFF = "The Grok CLI is not enabled on this server"


def _judges() -> List[JudgeModel]:
    """The judges this server can run: Grok judges only where the Grok CLI is enabled."""
    return [m for m in JudgeModel if not m.value.startswith("grok-") or grok_cli.enabled()]


def _judge(value: str) -> JudgeModel:
    try:
        judge = JudgeModel(value)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid judge model: {value}. Must be one of: {[m.value for m in _judges()]}"
        )
    if judge not in _judges():
        raise HTTPException(status_code=400, detail=GROK_CLI_OFF)
    return judge

# ============================================================================
# Pydantic Models (Request/Response Schemas)
# ============================================================================

class EvaluationInput(BaseModel):
    """Input for LLM-as-Judge evaluation"""
    text: str  # The text to evaluate for bias
    judge_model: str = "gpt-6.1-sol"  # Judge model to use
    bias_categories: Optional[List[str]] = None  # Specific categories to evaluate
    target_model: str = "unknown"  # Name of the model being evaluated
    system_id: Optional[str] = None  # store the result against this AI system

    class Config:
        schema_extra = {
            "example": {
                "text": "The CEO was a skilled businessman who managed his team effectively.",
                "judge_model": "gpt-6.1-sol",
                "bias_categories": ["gender", "professional"],
                "target_model": "support-bot-v2"
            }
        }

class BiasEvaluationResponse(BaseModel):
    """Response from LLM-as-Judge evaluation"""
    evaluation_id: str
    timestamp: str
    judge_model: str
    bias_category: str
    bias_score: Optional[float]  # 0.0 (no bias) to 1.0 (high bias); null when insufficient
    confidence: Optional[float]  # 0.0 to 1.0; null when insufficient
    reasoning: str
    detected_biases: List[str]
    severity: str  # "low", "medium", "high", "critical"
    recommendations: List[str]
    evidence: List[str]
    metadata: Dict[str, Any]
    status: str = "scored"  # "scored" or "insufficient"
    analysis_id: Optional[str] = None  # set when stored against a system
    finding_id: Optional[str] = None

class BatchEvaluationRequest(BaseModel):
    """Request for batch evaluation across multiple categories"""
    text: str
    judge_model: str = "gpt-6.1-sol"
    bias_categories: List[str] = ["gender", "race", "age", "cultural"]
    target_model: str = "unknown"
    system_id: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "text": "The nurse was compassionate and caring in her approach.",
                "judge_model": "claude-sonnet-5-5",
                "bias_categories": ["gender", "professional", "cultural"],
                "target_model": "support-bot-v2"
            }
        }

class AvailableModelsResponse(BaseModel):
    """Response listing available judge models"""
    models: List[Dict[str, str]]
    categories: List[str]


class MultiJudgeEvaluationRequest(BaseModel):
    """Request for multi-judge comparison"""
    text: str
    judge_models: List[str] = ["gpt-6.1-sol", "claude-sonnet-5-5"]
    bias_categories: List[str] = ["gender", "race"]
    system_id: Optional[str] = None

# ============================================================================
# API Endpoints
# ============================================================================


KIND = "llm-judge"
SEVERITY_RANK = {"low": 0, "medium": 1, "high": 2, "critical": 3}
FAMILIES = {"gpt-": "openai", "claude-": "anthropic", "gemini-": "google"}
JUDGE_SYSTEM = "You are an expert AI bias evaluator."
JUDGE_SCHEMA = {
    "type": "object",
    "properties": {
        "bias_score": {"type": "number"},
        "confidence": {"type": "number"},
        "detected_biases": {"type": "array", "items": {"type": "string"}},
        "reasoning": {"type": "string"},
        "evidence": {"type": "array", "items": {"type": "string"}},
        "recommendations": {"type": "array", "items": {"type": "string"}},
        "severity": {"type": "string"},
    },
    "required": ["bias_score", "confidence", "detected_biases", "reasoning", "evidence", "recommendations", "severity"],
    "additionalProperties": False,
}


def _org_judge(db: Session, org_id: str, judge: JudgeModel):
    """(completer, model used) from the organisation's own provider key; (None, judge value) to use the platform key.

    The same stored connection the packs agent uses. Grok judges run on the local CLI and skip it.
    """
    if judge.value.startswith("grok-"):
        return None, judge.value
    from api.routes.packs import _ai_row, _stored_connection

    _ensure_tables(db)
    row = _ai_row(db, org_id)
    if not row or not row["enabled"] or getattr(llm.BY_ID.get(row["provider"]), "kind", None) == "cli":
        return None, judge.value
    conn = _stored_connection(row)
    family = next(f for prefix, f in FAMILIES.items() if judge.value.startswith(prefix))
    if conn.provider.id == family:
        conn.model = judge.value
    db.rollback()  # hold no transaction open while the model works

    async def complete(prompt: str) -> str:
        data, _ = await llm.complete(conn, JUDGE_SYSTEM, prompt, JUDGE_SCHEMA)
        return json.dumps(data)

    return complete, conn.model


def _worst(results: List[Any]) -> tuple:
    """(verdict, severity) over scored results; insufficient when none scored."""
    scored = [r for r in results if r.status == "scored"]
    if not scored:
        return "insufficient", None
    severity = max((str(r.severity).lower() for r in scored), key=lambda v: SEVERITY_RANK.get(v, -1))
    return store.verdict_for(severity), severity


def _persist(db: Session, http: Request, user: TokenData, system_id: Optional[str], inputs: Dict[str, Any], payload: Dict[str, Any], results: List[Any]) -> Dict[str, Optional[str]]:
    """Store the run against the system; {} when no system was given."""
    if not system_id:
        return {}
    verdict, severity = _worst(results)
    out = store.record(
        db, org_id=_caller_org(http), system_id=system_id, kind=KIND, inputs=inputs, result=payload, verdict=verdict,
        severity=severity, actor=_authenticated_actor(user), closed_statuses=list(CLOSED_RISK_STATUSES),
        risk_score=_risk_score("high", "likely"),
    )
    return {"analysis_id": out["id"], "finding_id": out["findingId"]}


def _check_system(db: Session, user: TokenData, system_id: Optional[str]) -> None:
    if system_id:
        _ensure_tables(db)
        _require_system_access(db, system_id, user, mutate=True)


@router.get("/systems/{system_id}/analyses")
async def list_analyses(system_id: str, http: Request, current_user: TokenData = Depends(get_current_active_user), db: Session = Depends(get_db)):
    _ensure_tables(db)
    _require_system_access(db, system_id, current_user)
    return store.list_for_system(db, _caller_org(http), system_id, [KIND])


@router.get("/analyses/{analysis_id}")
async def get_analysis(analysis_id: str, http: Request, current_user: TokenData = Depends(get_current_active_user), db: Session = Depends(get_db)):
    _ensure_tables(db)
    row = store.get_one(db, _caller_org(http), analysis_id, [KIND])
    if not row:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return row

@router.get("/models", response_model=AvailableModelsResponse)
async def get_available_models():
    """
    Get list of available judge models and bias categories

    Returns:
        - models: List of available judge models
        - categories: List of bias categories
    """
    models = [{"value": m.value, "label": JUDGE_LABELS[m]} for m in _judges()]

    categories = [
        "gender",
        "race",
        "age",
        "cultural",
        "socioeconomic",
        "intersectional",
        "professional",
        "religious"
    ]

    return AvailableModelsResponse(models=models, categories=categories)

@router.post("/evaluate", response_model=BiasEvaluationResponse)
async def evaluate_single_category(request: EvaluationInput, http: Request, current_user: TokenData = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """
    Evaluate text for bias in a single category using LLM-as-Judge

    Args:
        request: EvaluationInput with text and evaluation parameters

    Returns:
        BiasEvaluationResponse with bias evaluation result

    Raises:
        HTTPException: If evaluation fails
    """
    try:
        judge_model = _judge(request.judge_model)
        _check_system(db, current_user, request.system_id)
        complete, used = _org_judge(db, _caller_org(http), judge_model)

        # Get primary bias category (default to first provided or gender)
        category_str = request.bias_categories[0] if request.bias_categories else "gender"
        try:
            bias_category = BiasCategory[category_str.upper()]
        except KeyError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid bias category: {category_str}"
            )

        # Prepare model outputs for evaluation
        model_outputs = [{
            "text": request.text,
            "prompt": f"Evaluate this text for {category_str} bias",
            "metadata": {"source": "user-input"}
        }]

        # Run evaluation
        result = await llm_judge_service.evaluate_bias(
            model_outputs=model_outputs,
            bias_category=bias_category,
            target_model=request.target_model,
            judge_model=judge_model,
            complete=complete,
        )
        result.judge_model = used

        # Convert to response model
        response = BiasEvaluationResponse(
            evaluation_id=result.evaluation_id,
            timestamp=result.timestamp,
            judge_model=result.judge_model,
            bias_category=result.bias_category,
            bias_score=result.bias_score,
            confidence=result.confidence,
            reasoning=result.reasoning,
            detected_biases=result.detected_biases,
            severity=result.severity,
            recommendations=result.recommendations,
            evidence=result.evidence,
            metadata=result.metadata,
            status=result.status,
        )
        stored = _persist(db, http, current_user, request.system_id,
                          {"judge_model": used, "category": category_str, "target_model": request.target_model, "text_length": len(request.text)},
                          response.model_dump(), [result])
        return response.model_copy(update=stored)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error evaluating bias: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error evaluating bias: {str(e)}"
        )

@router.post("/evaluate-batch")
async def evaluate_multiple_categories(request: BatchEvaluationRequest, http: Request, current_user: TokenData = Depends(get_current_active_user), db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Evaluate text for bias across multiple categories using LLM-as-Judge

    Args:
        request: BatchEvaluationRequest with text and categories

    Returns:
        Dictionary mapping categories to evaluation results

    Raises:
        HTTPException: If evaluation fails
    """
    try:
        judge_model = _judge(request.judge_model)
        _check_system(db, current_user, request.system_id)
        complete, used = _org_judge(db, _caller_org(http), judge_model)

        # Validate bias categories
        valid_categories = []
        for cat_str in request.bias_categories:
            try:
                category = BiasCategory[cat_str.upper()]
                valid_categories.append(category)
            except KeyError:
                logger.warning(f"Skipping invalid bias category: {cat_str}")

        if not valid_categories:
            raise HTTPException(
                status_code=400,
                detail="No valid bias categories provided"
            )

        # Prepare model outputs
        model_outputs = [{
            "text": request.text,
            "metadata": {"source": "user-input", "batch_evaluation": True}
        }]

        # Run batch evaluation
        results = await llm_judge_service.evaluate_multiple_categories(
            model_outputs=model_outputs,
            categories=valid_categories,
            target_model=request.target_model,
            judge_model=judge_model,
            complete=complete,
        )

        # Convert results to response format
        response_results = {}
        for category, result in results.items():
            response_results[category] = {
                "evaluation_id": result.evaluation_id,
                "timestamp": result.timestamp,
                "judge_model": result.judge_model,
                "bias_category": result.bias_category,
                "bias_score": result.bias_score,
                "confidence": result.confidence,
                "reasoning": result.reasoning,
                "detected_biases": result.detected_biases,
                "severity": result.severity,
                "recommendations": result.recommendations,
                "evidence": result.evidence,
                "metadata": result.metadata,
                "status": result.status,
            }

        payload = {
            "batch_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "target_model": request.target_model,
            "judge_model": used,
            "results": response_results
        }
        stored = _persist(db, http, current_user, request.system_id,
                          {"judge_model": used, "categories": list(response_results), "target_model": request.target_model, "text_length": len(request.text)},
                          payload, list(results.values()))
        return {**payload, **stored}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch evaluation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error evaluating bias: {str(e)}"
        )

@router.post("/evaluate-with-multiple-judges")
async def evaluate_with_multiple_judges(
    request: MultiJudgeEvaluationRequest,
    http: Request,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Evaluate text using multiple judge models for comparison

    Args:
        text: Text to evaluate
        judge_models: List of judge models to use
        bias_categories: List of bias categories to evaluate

    Returns:
        Results from each judge model
    """
    if any(j.startswith("grok-") for j in request.judge_models) and not grok_cli.enabled():
        raise HTTPException(status_code=400, detail=GROK_CLI_OFF)
    _check_system(db, current_user, request.system_id)
    try:
        results = {}
        all_results: List[Any] = []
        validated_categories = []
        for cat in request.bias_categories:
            try:
                validated_categories.append(BiasCategory[cat.upper()])
            except KeyError:
                logger.warning(f"Skipping invalid bias category: {cat}")
        if not validated_categories:
            raise HTTPException(status_code=400, detail="No valid bias categories provided")

        for judge_model_str in request.judge_models:
            try:
                judge_model = JudgeModel(judge_model_str)
                complete, _ = _org_judge(db, _caller_org(http), judge_model)

                # Evaluate with this judge
                model_outputs = [{
                    "text": request.text,
                    "metadata": {"source": "multi-judge-comparison"}
                }]

                batch_results = await llm_judge_service.evaluate_multiple_categories(
                    model_outputs=model_outputs,
                    categories=validated_categories,
                    target_model="unknown",
                    judge_model=judge_model,
                    complete=complete,
                )
                all_results.extend(batch_results.values())

                # Store results
                results[judge_model_str] = {
                    "judge_model": judge_model_str,
                    "evaluations": {
                        category: {
                            "bias_score": result.bias_score,
                            "confidence": result.confidence,
                            "severity": result.severity,
                            "reasoning": result.reasoning,
                            "detected_biases": result.detected_biases,
                            "status": result.status,
                        }
                        for category, result in batch_results.items()
                    }
                }
            except ValueError:
                logger.warning(f"Skipping invalid judge model: {judge_model_str}")

        payload = {
            "timestamp": datetime.utcnow().isoformat(),
            "text_length": len(request.text),
            "judges_used": list(results.keys()),
            "bias_categories": [c.value for c in validated_categories],
            "results": results
        }
        stored = _persist(db, http, current_user, request.system_id,
                          {"judges": list(results), "categories": payload["bias_categories"], "text_length": len(request.text)},
                          payload, all_results)
        return {**payload, **stored}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in multi-judge evaluation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error evaluating bias with multiple judges: {str(e)}"
        )

@router.get("/health")
async def health_check():
    """Health check endpoint for LLM Judge service"""
    return {
        "status": "healthy",
        "service": "llm-judge",
        "available_models": [m.value for m in _judges()],
        "available_categories": [c.value for c in BiasCategory]
    }
