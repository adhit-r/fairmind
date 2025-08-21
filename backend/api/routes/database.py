"""
Database API Routes - Real data from Supabase/Prisma
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import logging
from datetime import datetime

from ..services.database_service import database_service

router = APIRouter(prefix="/database", tags=["database"])

logger = logging.getLogger(__name__)

@router.get("/profiles")
async def get_profiles(limit: int = 10):
    """Get user profiles from database"""
    try:
        profiles = await database_service.get_profiles(limit)
        return {
            "success": True,
            "data": profiles,
            "count": len(profiles)
        }
    except Exception as e:
        logger.error(f"Error getting profiles: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/bias-analyses")
async def get_bias_analyses(limit: int = 10):
    """Get geographic bias analyses from database"""
    try:
        analyses = await database_service.get_geographic_bias_analyses(limit)
        return {
            "success": True,
            "data": analyses,
            "count": len(analyses)
        }
    except Exception as e:
        logger.error(f"Error getting bias analyses: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/audit-logs")
async def get_audit_logs(limit: int = 10):
    """Get audit logs from database"""
    try:
        logs = await database_service.get_audit_logs(limit)
        return {
            "success": True,
            "data": logs,
            "count": len(logs)
        }
    except Exception as e:
        logger.error(f"Error getting audit logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/country-metrics")
async def get_country_metrics(limit: int = 10):
    """Get country performance metrics from database"""
    try:
        metrics = await database_service.get_country_performance_metrics(limit)
        return {
            "success": True,
            "data": metrics,
            "count": len(metrics)
        }
    except Exception as e:
        logger.error(f"Error getting country metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboard-stats")
async def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        stats = await database_service.get_dashboard_stats()
        return {
            "success": True,
            "data": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def database_health():
    """Check database connectivity"""
    try:
        # Try to get a small amount of data to test connectivity
        profiles = await database_service.get_profiles(1)
        return {
            "success": True,
            "status": "connected",
            "message": "Database is accessible",
            "test_query_count": len(profiles)
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "success": False,
            "status": "disconnected", 
            "message": str(e)
        }

@router.get("/test-script")
async def test_script():
    """Test the Node.js script directly"""
    try:
        result = await database_service._run_prisma_script("test-simple.js")
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        logger.error(f"Script test failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }
