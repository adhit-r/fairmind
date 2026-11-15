"""
Database API Routes - Real data from Supabase/Prisma
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
import logging
from datetime import datetime
from sqlalchemy import text
import json

# Direct access to database manager instead of broken service
from database.connection import db_manager
from config.settings import settings
from api.routes.org_scope import ORG_MEMBER_USER_IDS, org_member, plain_id
from core.middleware.audit import NOT_A_READ
from src.application.services.governance_assurance_service import OrgMembership

# Every read is limited to the caller's organisation (org_id columns, or the
# organisation's active members for tables that only record a user).
router = APIRouter(prefix="/database", tags=["database"], dependencies=[Depends(org_member)])

# Additional router for main API endpoints (without /database prefix)
main_router = APIRouter(tags=["main-api"], dependencies=[Depends(org_member)])

logger = logging.getLogger(__name__)


def _fail(what: str, e: Exception) -> HTTPException:
    """A database failure is an error, never an empty success."""
    logger.error(f"Error getting {what}: {e}")
    return HTTPException(status_code=500, detail=f"Could not read {what}; see the server log")


@router.get("/profiles")
def get_profiles(limit: int = 10, m: OrgMembership = Depends(org_member)):
    """User profiles of this organisation's members."""
    try:
        with db_manager.get_session() as session:
            rows = session.execute(text(f"""
                SELECT id, username, full_name, avatar_url, role, created_at
                FROM profiles
                WHERE {plain_id('id')} IN ({ORG_MEMBER_USER_IDS})
                LIMIT :limit
            """), {"org_id": m.org_id, "limit": limit}).fetchall()
        profiles_data = [{
            "id": str(row.id),
            "username": row.username,
            "full_name": row.full_name,
            "avatar_url": row.avatar_url,
            "role": row.role,
            "created_at": str(row.created_at),
        } for row in rows]
        return {"success": True, "data": profiles_data, "count": len(profiles_data)}
    except Exception as e:
        raise _fail("profiles", e)

@router.get("/bias-analyses")
def get_bias_analyses(limit: int = 10, m: OrgMembership = Depends(org_member)):
    """Geographic bias analyses of this organisation."""
    try:
        with db_manager.get_session() as session:
            rows = session.execute(text("""
                SELECT id, model_id, source_country, target_country, bias_score, risk_level, analysis_date
                FROM geographic_bias_analyses
                WHERE org_id = :org_id
                ORDER BY analysis_date DESC
                LIMIT :limit
            """), {"org_id": m.org_id, "limit": limit}).fetchall()
        analyses_data = [{
            "id": str(row.id),
            "modelId": row.model_id,
            "sourceCountry": row.source_country,
            "targetCountry": row.target_country,
            "biasScore": row.bias_score,
            "riskLevel": row.risk_level,
            "analysisDate": str(row.analysis_date),
        } for row in rows]
        return {"success": True, "data": analyses_data, "count": len(analyses_data)}
    except Exception as e:
        raise _fail("bias analyses", e)

@router.get("/audit-logs")
def get_audit_logs(limit: int = 10, m: OrgMembership = Depends(org_member)):
    """Audit log entries of this organisation."""
    try:
        with db_manager.get_session() as session:
            rows = session.execute(text("""
                SELECT id, user_id, action, resource_type, resource_id, details, ip_address, created_at
                FROM audit_logs
                WHERE org_id = :org_id
                ORDER BY created_at DESC
                LIMIT :limit
            """), {"org_id": m.org_id, "limit": limit}).fetchall()
        logs_data = []
        for row in rows:
            details = row.details
            if isinstance(details, str):
                try:
                    details = json.loads(details)
                except ValueError:
                    pass
            logs_data.append({
                "id": str(row.id),
                "userId": str(row.user_id),
                "action": row.action,
                "resourceType": row.resource_type,
                "resourceId": row.resource_id,
                "details": details,
                "ipAddress": str(row.ip_address),
                "timestamp": str(row.created_at),
            })
        return {"success": True, "data": logs_data, "count": len(logs_data)}
    except Exception as e:
        raise _fail("audit logs", e)

@router.get("/country-metrics")
def get_country_metrics(limit: int = 10, m: OrgMembership = Depends(org_member)):
    """Country performance metrics. Not built yet."""
    raise HTTPException(status_code=501, detail="Country metrics are not available yet.")

@router.get("/dashboard-stats")
def get_dashboard_stats(m: OrgMembership = Depends(org_member)):
    """Dashboard counts for this organisation; any failed query fails the request."""
    try:
        with db_manager.get_session() as session:
            org = {"org_id": m.org_id}
            total_models = session.execute(
                text("SELECT COUNT(*) FROM models WHERE status = 'active' AND org_id = :org_id"), org
            ).scalar() or 0
            total_datasets = session.execute(
                text("SELECT COUNT(*) FROM datasets WHERE org_id = :org_id"), org
            ).scalar() or 0
            active_scans = session.execute(text("""
                SELECT COUNT(*) FROM geographic_bias_analyses
                WHERE org_id = :org_id
                AND (compliance_status != 'completed' OR compliance_status IS NULL)
            """), org).scalar() or 0
            rows = session.execute(text(f"""
                SELECT id, action, resource_type, resource_id, created_at, user_id
                FROM audit_logs
                WHERE org_id = :org_id AND {NOT_A_READ}
                ORDER BY created_at DESC
                LIMIT 5
            """), org).fetchall()
        activity = [{
            "id": str(row.id),
            "type": row.action or "unknown",
            "description": f"{row.action or 'Action'} on {row.resource_type}" if row.resource_type else str(row.action or "Activity"),
            "timestamp": row.created_at.isoformat() if hasattr(row.created_at, "isoformat") else str(row.created_at),
            "user": str(row.user_id) if row.user_id else "System",
        } for row in rows]
        stats = {
            "totalModels": total_models,
            "totalDatasets": total_datasets,
            "activeScans": active_scans,
            "recentActivity": activity,
            # Every query above answered, so the database is reachable.
            "systemHealth": {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "version": settings.api_version,
            },
        }
        return {"success": True, "data": stats, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        raise _fail("dashboard stats", e)

@router.get("/models")
def get_models(m: OrgMembership = Depends(org_member)):
    """Get this organisation's models for frontend display from database"""
    try:
        models_data = []
        
        with db_manager.get_session() as session:
            result = session.execute(text("""
                SELECT id, name, description, model_type, version, status,
                       tags, metadata, upload_date, updated_at
                FROM models
                WHERE status = 'active' AND org_id = :org_id
                ORDER BY upload_date DESC
            """), {"org_id": m.org_id})
            
            for row in result:
                # Parse JSON fields
                tags = row.tags if row.tags else []
                metadata = row.metadata if row.metadata else {}
                if isinstance(metadata, str):
                    try:
                        metadata = json.loads(metadata)
                    except:
                        metadata = {}
                
                # Extract accuracy from metadata if available
                accuracy = metadata.get("accuracy", metadata.get("r2_score"))
                
                # Handle dates
                def format_date(date_value):
                    return None if date_value is None else str(date_value)
                
                model_dict = {
                    "id": str(row.id),
                    "name": row.name,
                    "description": row.description,
                    "type": row.model_type,
                    "version": row.version,
                    "status": "active" if row.status else "inactive",
                    "accuracy": float(accuracy) if isinstance(accuracy, (int, float)) else None,
                    # Only scores recorded in the model's metadata; never a default.
                    "bias_score": metadata.get("bias_score") if isinstance(metadata.get("bias_score"), (int, float)) else None,
                    "fairness_score": metadata.get("fairness_score") if isinstance(metadata.get("fairness_score"), (int, float)) else None,
                    "created_at": format_date(row.upload_date),
                    "updated_at": format_date(row.updated_at),
                    "tags": tags,
                    "metadata": metadata
                }
                models_data.append(model_dict)
        
        return {
            "success": True,
            "data": models_data,
            "count": len(models_data),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
def database_health():
    """Check database connectivity"""
    try:
        with db_manager.get_session() as session:
            session.execute(text("SELECT 1"))
        return {
            "success": True,
            "status": "connected",
            "message": "Database is accessible"
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "success": False,
            "status": "disconnected",
            "message": "Database is not reachable; see the server log"
        }

# Main API endpoints (accessible at /api/v1/*)
@main_router.get("/models")
def get_models_main(m: OrgMembership = Depends(org_member)):
    return get_models(m)
