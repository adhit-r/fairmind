"""
AI Governance API Routes
Comprehensive API endpoints for AI governance, compliance, and explainability
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import json
import logging
from pathlib import Path

from ..services.policy_engine import PolicyEngine, PolicyRule, ComplianceResult
from ..services.compliance_mapper import ComplianceMapper, FrameworkAssessment
from ..services.lifecycle_integration import LifecycleIntegration, LifecycleContext, LifecycleStage
from ..services.evidence_collector import EvidenceCollector, EvidenceType, ReportFormat
from ..services.risk_incident_manager import RiskIncidentManager, RiskLevel, IncidentStatus, AlertChannel
from ..services.generative_ai_explainability import GenerativeAIExplainability, ModelType, ExplainabilityMethod, BiasCategory

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize services
policy_engine = PolicyEngine()
compliance_mapper = ComplianceMapper()
lifecycle_integration = LifecycleIntegration(policy_engine, compliance_mapper)
evidence_collector = EvidenceCollector()
risk_incident_manager = RiskIncidentManager()
generative_ai_explainability = GenerativeAIExplainability()

# Policy Management Endpoints
@router.post("/policies")
async def create_policy_rule(rule_data: Dict[str, Any]):
    """Create a new policy rule"""
    try:
        rule = policy_engine.create_policy_rule(rule_data)
        return {
            "success": True,
            "rule_id": rule.id,
            "message": "Policy rule created successfully"
        }
    except Exception as e:
        logger.error(f"Error creating policy rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/policies")
async def get_policy_rules(framework: Optional[str] = None):
    """Get policy rules, optionally filtered by framework"""
    try:
        if framework:
            rules = policy_engine.get_rules_by_framework(framework)
        else:
            rules = policy_engine.get_all_rules()
        
        return {
            "success": True,
            "rules": [rule.__dict__ for rule in rules],
            "count": len(rules)
        }
    except Exception as e:
        logger.error(f"Error getting policy rules: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/policies/{rule_id}/evaluate")
async def evaluate_policy_rule(rule_id: str, context: Dict[str, Any]):
    """Evaluate a policy rule against context"""
    try:
        if rule_id not in policy_engine.rules:
            raise HTTPException(status_code=404, detail="Policy rule not found")
        
        rule = policy_engine.rules[rule_id]
        
        if rule.rule_type == "rego":
            result = policy_engine.evaluate_rego_policy(rule, context)
        elif rule.rule_type == "dsl":
            result = policy_engine.evaluate_dsl_policy(rule, context)
        else:
            raise HTTPException(status_code=400, detail="Unsupported rule type")
        
        return {
            "success": True,
            "result": result.__dict__
        }
    except Exception as e:
        logger.error(f"Error evaluating policy rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/compliance/assess")
async def assess_compliance(system_id: str, framework: str, context: Dict[str, Any]):
    """Assess system compliance with a framework"""
    try:
        result = compliance_mapper.assess_framework_compliance(system_id, framework, context)
        return {
            "success": True,
            "assessment": result.__dict__
        }
    except Exception as e:
        logger.error(f"Error assessing compliance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/compliance/frameworks")
async def get_supported_frameworks():
    """Get supported regulatory frameworks"""
    try:
        frameworks = list(compliance_mapper.regulatory_frameworks.keys())
        return {
            "success": True,
            "frameworks": frameworks,
            "count": len(frameworks)
        }
    except Exception as e:
        logger.error(f"Error getting frameworks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/compliance/frameworks/{framework}/controls")
async def get_framework_controls(framework: str):
    """Get controls for a specific framework"""
    try:
        controls = compliance_mapper.get_framework_controls(framework)
        return {
            "success": True,
            "framework": framework,
            "controls": {k: v.__dict__ for k, v in controls.items()},
            "count": len(controls)
        }
    except Exception as e:
        logger.error(f"Error getting framework controls: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Lifecycle Integration Endpoints
@router.post("/lifecycle/process")
async def process_lifecycle_stage(
    system_id: str,
    project_id: str,
    user_id: str,
    stage: str,
    data: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """Process a lifecycle stage with governance checks"""
    try:
        # Convert stage string to enum
        try:
            lifecycle_stage = LifecycleStage(stage)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid lifecycle stage: {stage}")
        
        # Create lifecycle context
        context = LifecycleContext(
            system_id=system_id,
            project_id=project_id,
            user_id=user_id,
            stage=lifecycle_stage,
            data=data,
            metadata={"api_request": True},
            created_at=datetime.now()
        )
        
        # Process stage
        result = await lifecycle_integration.process_lifecycle_stage(context)
        
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        logger.error(f"Error processing lifecycle stage: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/lifecycle/{system_id}/summary")
async def get_lifecycle_summary(system_id: str):
    """Get lifecycle summary for a system"""
    try:
        summary = lifecycle_integration.get_lifecycle_summary(system_id)
        return {
            "success": True,
            "summary": summary
        }
    except Exception as e:
        logger.error(f"Error getting lifecycle summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/lifecycle/checks")
async def get_available_checks(stage: Optional[str] = None):
    """Get available lifecycle checks"""
    try:
        if stage:
            try:
                lifecycle_stage = LifecycleStage(stage)
                checks = lifecycle_integration.get_available_checks(lifecycle_stage)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid lifecycle stage: {stage}")
        else:
            checks = lifecycle_integration.get_available_checks()
        
        return {
            "success": True,
            "checks": [check.__dict__ for check in checks],
            "count": len(checks)
        }
    except Exception as e:
        logger.error(f"Error getting available checks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Evidence Collection Endpoints
@router.post("/evidence/collect")
async def collect_evidence(
    name: str,
    description: str,
    evidence_type: str,
    system_id: str,
    framework: str,
    control_id: str,
    content: str,
    content_type: str = "text/plain",
    expires_in_days: Optional[int] = None
):
    """Collect compliance evidence"""
    try:
        # Convert evidence type string to enum
        try:
            evidence_type_enum = EvidenceType(evidence_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid evidence type: {evidence_type}")
        
        evidence_item = evidence_collector.collect_evidence(
            name=name,
            description=description,
            evidence_type=evidence_type_enum,
            system_id=system_id,
            framework=framework,
            control_id=control_id,
            content=content,
            content_type=content_type,
            expires_in_days=expires_in_days
        )
        
        return {
            "success": True,
            "evidence_id": evidence_item.id,
            "message": "Evidence collected successfully"
        }
    except Exception as e:
        logger.error(f"Error collecting evidence: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/evidence/upload")
async def upload_evidence_file(
    file: UploadFile = File(...),
    name: str = None,
    description: str = "",
    evidence_type: str = "document",
    system_id: str = "",
    framework: str = "",
    control_id: str = "",
    expires_in_days: Optional[int] = None
):
    """Upload evidence file"""
    try:
        # Read file content
        content = await file.read()
        
        # Use filename as name if not provided
        if not name:
            name = file.filename
        
        # Convert evidence type string to enum
        try:
            evidence_type_enum = EvidenceType(evidence_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid evidence type: {evidence_type}")
        
        evidence_item = evidence_collector.collect_evidence(
            name=name,
            description=description,
            evidence_type=evidence_type_enum,
            system_id=system_id,
            framework=framework,
            control_id=control_id,
            content=content,
            content_type=file.content_type or "application/octet-stream",
            expires_in_days=expires_in_days
        )
        
        return {
            "success": True,
            "evidence_id": evidence_item.id,
            "message": "Evidence file uploaded successfully"
        }
    except Exception as e:
        logger.error(f"Error uploading evidence file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/evidence/{system_id}")
async def get_evidence_by_system(system_id: str, framework: Optional[str] = None):
    """Get evidence items for a system"""
    try:
        evidence = evidence_collector.get_evidence_by_system(system_id, framework)
        return {
            "success": True,
            "evidence": [item.__dict__ for item in evidence],
            "count": len(evidence)
        }
    except Exception as e:
        logger.error(f"Error getting evidence: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/evidence/collections")
async def create_evidence_collection(
    name: str,
    description: str,
    system_id: str,
    framework: str,
    purpose: str,
    evidence_item_ids: List[str] = None
):
    """Create an evidence collection"""
    try:
        collection = evidence_collector.create_evidence_collection(
            name=name,
            description=description,
            system_id=system_id,
            framework=framework,
            purpose=purpose,
            evidence_item_ids=evidence_item_ids
        )
        
        return {
            "success": True,
            "collection_id": collection.id,
            "message": "Evidence collection created successfully"
        }
    except Exception as e:
        logger.error(f"Error creating evidence collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reports/generate")
async def generate_compliance_report(
    title: str,
    system_id: str,
    framework: str,
    report_type: str,
    evidence_collection_ids: List[str],
    summary: Dict[str, Any],
    findings: List[Dict[str, Any]],
    recommendations: List[str],
    generated_by: str
):
    """Generate a compliance report"""
    try:
        report = evidence_collector.generate_compliance_report(
            title=title,
            system_id=system_id,
            framework=framework,
            report_type=report_type,
            evidence_collection_ids=evidence_collection_ids,
            summary=summary,
            findings=findings,
            recommendations=recommendations,
            generated_by=generated_by
        )
        
        return {
            "success": True,
            "report_id": report.id,
            "message": "Compliance report generated successfully"
        }
    except Exception as e:
        logger.error(f"Error generating compliance report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reports/{report_id}/export")
async def export_report(report_id: str, format: str = "json"):
    """Export compliance report"""
    try:
        # Convert format string to enum
        try:
            report_format = ReportFormat(format.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid report format: {format}")
        
        result = evidence_collector.export_report(report_id, report_format)
        
        if report_format == ReportFormat.PDF:
            # Return PDF as file response
            return FileResponse(
                path=result,
                filename=f"compliance_report_{report_id}.pdf",
                media_type="application/pdf"
            )
        else:
            # Return other formats as JSON
            return {
                "success": True,
                "format": format,
                "content": result
            }
    except Exception as e:
        logger.error(f"Error exporting report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Risk and Incident Management Endpoints
@router.post("/risks/assess")
async def create_risk_assessment(
    system_id: str,
    risk_name: str,
    description: str,
    risk_level: str,
    category: str,
    probability: float,
    impact: float,
    mitigation_measures: List[str],
    assessed_by: str,
    next_review_days: int = 90
):
    """Create a risk assessment"""
    try:
        # Convert risk level string to enum
        try:
            risk_level_enum = RiskLevel(risk_level.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid risk level: {risk_level}")
        
        assessment = risk_incident_manager.create_risk_assessment(
            system_id=system_id,
            risk_name=risk_name,
            description=description,
            risk_level=risk_level_enum,
            category=category,
            probability=probability,
            impact=impact,
            mitigation_measures=mitigation_measures,
            assessed_by=assessed_by,
            next_review_days=next_review_days
        )
        
        return {
            "success": True,
            "assessment_id": assessment.id,
            "message": "Risk assessment created successfully"
        }
    except Exception as e:
        logger.error(f"Error creating risk assessment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/incidents")
async def create_incident(
    title: str,
    description: str,
    system_id: str,
    priority: str,
    risk_level: str,
    category: str,
    reported_by: str,
    affected_users: int = 0,
    business_impact: str = ""
):
    """Create an incident"""
    try:
        # Convert priority and risk level strings to enums
        try:
            priority_enum = IncidentPriority(priority.lower())
            risk_level_enum = RiskLevel(risk_level.lower())
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid priority or risk level: {e}")
        
        incident = risk_incident_manager.create_incident(
            title=title,
            description=description,
            system_id=system_id,
            priority=priority_enum,
            risk_level=risk_level_enum,
            category=category,
            reported_by=reported_by,
            affected_users=affected_users,
            business_impact=business_impact
        )
        
        return {
            "success": True,
            "incident_id": incident.id,
            "message": "Incident created successfully"
        }
    except Exception as e:
        logger.error(f"Error creating incident: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/incidents/{incident_id}/status")
async def update_incident_status(
    incident_id: str,
    status: str,
    assigned_to: Optional[str] = None,
    resolution_notes: Optional[str] = None,
    root_cause: Optional[str] = None,
    prevention_measures: List[str] = None
):
    """Update incident status"""
    try:
        # Convert status string to enum
        try:
            status_enum = IncidentStatus(status.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid incident status: {status}")
        
        success = risk_incident_manager.update_incident_status(
            incident_id=incident_id,
            status=status_enum,
            assigned_to=assigned_to,
            resolution_notes=resolution_notes,
            root_cause=root_cause,
            prevention_measures=prevention_measures
        )
        
        if success:
            return {
                "success": True,
                "message": "Incident status updated successfully"
            }
        else:
            raise HTTPException(status_code=404, detail="Incident not found")
    except Exception as e:
        logger.error(f"Error updating incident status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboard/risk")
async def get_risk_dashboard():
    """Get risk dashboard data"""
    try:
        dashboard_data = risk_incident_manager.get_risk_dashboard_data()
        return {
            "success": True,
            "dashboard": dashboard_data
        }
    except Exception as e:
        logger.error(f"Error getting risk dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Generative AI Explainability Endpoints
@router.post("/ai-models/register")
async def register_ai_model(
    model_id: str,
    name: str,
    model_type: str,
    version: str,
    description: str,
    capabilities: List[str],
    input_format: str,
    output_format: str
):
    """Register a generative AI model"""
    try:
        # Convert model type string to enum
        try:
            model_type_enum = ModelType(model_type.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid model type: {model_type}")
        
        model = generative_ai_explainability.register_model(
            model_id=model_id,
            name=name,
            model_type=model_type_enum,
            version=version,
            description=description,
            capabilities=capabilities,
            input_format=input_format,
            output_format=output_format
        )
        
        return {
            "success": True,
            "model_id": model.id,
            "message": "AI model registered successfully"
        }
    except Exception as e:
        logger.error(f"Error registering AI model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ai-models/{model_id}/explainability")
async def analyze_explainability(
    model_id: str,
    prompt: str,
    method: str,
    parameters: Dict[str, Any] = None
):
    """Analyze explainability for an AI model"""
    try:
        # Convert method string to enum
        try:
            method_enum = ExplainabilityMethod(method.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid explainability method: {method}")
        
        result = await generative_ai_explainability.analyze_llm_explainability(
            model_id=model_id,
            prompt=prompt,
            method=method_enum,
            parameters=parameters
        )
        
        return {
            "success": True,
            "result": result.__dict__
        }
    except Exception as e:
        logger.error(f"Error analyzing explainability: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ai-models/{model_id}/bias-detection")
async def detect_bias(
    model_id: str,
    test_cases: List[Dict[str, Any]],
    bias_categories: List[str]
):
    """Detect bias in an AI model"""
    try:
        # Convert bias category strings to enums
        try:
            bias_category_enums = [BiasCategory(category.lower()) for category in bias_categories]
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid bias category: {e}")
        
        results = await generative_ai_explainability.detect_llm_bias(
            model_id=model_id,
            test_cases=test_cases,
            bias_categories=bias_category_enums
        )
        
        return {
            "success": True,
            "results": [result.__dict__ for result in results]
        }
    except Exception as e:
        logger.error(f"Error detecting bias: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ai-models/{model_id}/explainability/summary")
async def get_explainability_summary(model_id: str):
    """Get explainability summary for a model"""
    try:
        summary = generative_ai_explainability.get_explainability_summary(model_id)
        return {
            "success": True,
            "summary": summary
        }
    except Exception as e:
        logger.error(f"Error getting explainability summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ai-models/{model_id}/bias/summary")
async def get_bias_summary(model_id: str):
    """Get bias detection summary for a model"""
    try:
        summary = generative_ai_explainability.get_bias_summary(model_id)
        return {
            "success": True,
            "summary": summary
        }
    except Exception as e:
        logger.error(f"Error getting bias summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# System Status Endpoint
@router.get("/status")
async def get_system_status():
    """Get overall system status"""
    try:
        # Get statistics from all services
        evidence_stats = evidence_collector.get_evidence_statistics()
        risk_dashboard = risk_incident_manager.get_risk_dashboard_data()
        
        return {
            "success": True,
            "status": "operational",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "policy_engine": {
                    "status": "operational",
                    "rules_count": len(policy_engine.rules)
                },
                "compliance_mapper": {
                    "status": "operational",
                    "frameworks_count": len(compliance_mapper.regulatory_frameworks)
                },
                "lifecycle_integration": {
                    "status": "operational",
                    "checks_count": len(lifecycle_integration.checks)
                },
                "evidence_collector": {
                    "status": "operational",
                    "statistics": evidence_stats
                },
                "risk_incident_manager": {
                    "status": "operational",
                    "statistics": risk_dashboard
                },
                "generative_ai_explainability": {
                    "status": "operational",
                    "models_count": len(generative_ai_explainability.models)
                }
            }
        }
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

