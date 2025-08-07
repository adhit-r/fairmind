"""
Supabase client for FairMind backend
"""

import os
from typing import Dict, Any, List, Optional
try:
    from supabase import create_client, Client
except ImportError:
    # Fallback if supabase package is not installed
    create_client = None
    Client = None
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class SupabaseService:
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not self.supabase_url or not self.supabase_key or create_client is None:
            logger.warning("Supabase credentials not found or package not installed. Using mock data.")
            self.client = None
        else:
            try:
                self.client = create_client(self.supabase_url, self.supabase_key)
                logger.info("Supabase client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {e}")
                self.client = None
    
    def is_connected(self) -> bool:
        """Check if Supabase client is connected"""
        return self.client is not None
    
    async def insert_geographic_bias_analysis(self, analysis_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Insert a new geographic bias analysis"""
        if not self.is_connected():
            logger.warning("Supabase not connected. Skipping database insert.")
            return None
        
        try:
            # Prepare data for insertion
            insert_data = {
                "model_id": analysis_data["model_id"],
                "source_country": analysis_data["source_country"],
                "target_country": analysis_data["target_country"],
                "bias_detected": analysis_data["bias_detected"],
                "bias_score": analysis_data["bias_score"],
                "performance_drop": analysis_data["performance_drop"],
                "risk_level": analysis_data["risk_level"],
                "affected_metrics": analysis_data["affected_metrics"],
                "recommendations": analysis_data["recommendations"],
                "cultural_factors": analysis_data["cultural_factors"],
                "compliance_issues": analysis_data["compliance_issues"],
                "model_performance_data": analysis_data.get("model_performance_data", {}),
                "demographic_data": analysis_data.get("demographic_data", {}),
                "created_by": analysis_data.get("created_by"),
                "organization_id": analysis_data.get("organization_id")
            }
            
            result = self.client.table("geographic_bias_analyses").insert(insert_data).execute()
            
            if result.data:
                logger.info(f"Geographic bias analysis saved to database: {result.data[0]['id']}")
                return result.data[0]
            else:
                logger.error("Failed to insert geographic bias analysis")
                return None
                
        except Exception as e:
            logger.error(f"Error inserting geographic bias analysis: {e}")
            return None
    
    async def get_geographic_bias_analyses(self, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """Get recent geographic bias analyses"""
        if not self.is_connected():
            logger.warning("Supabase not connected. Returning mock data.")
            return []
        
        try:
            result = self.client.table("geographic_bias_analyses")\
                .select("*")\
                .order("created_at", desc=True)\
                .limit(limit)\
                .offset(offset)\
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error fetching geographic bias analyses: {e}")
            return []
    
    async def get_country_performance_metrics(self) -> List[Dict[str, Any]]:
        """Get country performance metrics"""
        if not self.is_connected():
            logger.warning("Supabase not connected. Returning mock data.")
            return []
        
        try:
            result = self.client.table("country_performance_metrics")\
                .select("*")\
                .order("last_updated", desc=True)\
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error fetching country performance metrics: {e}")
            return []
    
    async def get_geographic_bias_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data for geographic bias"""
        if not self.is_connected():
            logger.warning("Supabase not connected. Returning mock data.")
            return self._get_mock_dashboard_data()
        
        try:
            # Get total counts
            total_analyses = self.client.table("geographic_bias_analyses").select("id", count="exact").execute()
            biased_analyses = self.client.table("geographic_bias_analyses")\
                .select("id", count="exact")\
                .gte("bias_score", 0.3)\
                .execute()
            high_risk_analyses = self.client.table("geographic_bias_analyses")\
                .select("id", count="exact")\
                .in_("risk_level", ["HIGH", "CRITICAL"])\
                .execute()
            
            # Get recent analyses
            recent_analyses = self.client.table("geographic_bias_analyses")\
                .select("model_id, source_country, target_country, bias_score, risk_level, created_at")\
                .order("created_at", desc=True)\
                .limit(3)\
                .execute()
            
            # Get country performance
            country_performance = self.client.table("country_performance_metrics")\
                .select("*")\
                .execute()
            
            return {
                "total_models": total_analyses.count if total_analyses.count else 0,
                "models_with_geographic_bias": biased_analyses.count if biased_analyses.count else 0,
                "high_risk_deployments": high_risk_analyses.count if high_risk_analyses.count else 0,
                "countries_analyzed": len(country_performance.data) if country_performance.data else 0,
                "recent_analyses": recent_analyses.data if recent_analyses.data else [],
                "country_performance": {
                    item["country_code"]: {
                        "models_deployed": item["models_deployed"],
                        "avg_bias_score": item["avg_bias_score"],
                        "compliance_status": item["compliance_status"]
                    } for item in (country_performance.data or [])
                }
            }
            
        except Exception as e:
            logger.error(f"Error fetching dashboard data: {e}")
            return self._get_mock_dashboard_data()
    
    def _get_mock_dashboard_data(self) -> Dict[str, Any]:
        """Return mock dashboard data when database is not available"""
        from datetime import datetime, timedelta
        import random
        
        countries = ["USA", "UK", "Germany", "France", "Japan", "India", "Brazil", "Australia"]
        
        return {
            "total_models": 47,
            "models_with_geographic_bias": 12,
            "high_risk_deployments": 5,
            "countries_analyzed": len(countries),
            "recent_analyses": [
                {
                    "model_id": "credit-scoring-v1",
                    "source_country": "USA",
                    "target_country": "India",
                    "bias_score": 0.72,
                    "risk_level": "HIGH",
                    "created_at": datetime.now().isoformat()
                },
                {
                    "model_id": "fraud-detection-v2",
                    "source_country": "UK",
                    "target_country": "Brazil",
                    "bias_score": 0.45,
                    "risk_level": "MEDIUM",
                    "created_at": (datetime.now() - timedelta(hours=2)).isoformat()
                },
                {
                    "model_id": "recommendation-engine-v1",
                    "source_country": "USA",
                    "target_country": "Japan",
                    "bias_score": 0.89,
                    "risk_level": "CRITICAL",
                    "created_at": (datetime.now() - timedelta(hours=4)).isoformat()
                }
            ],
            "country_performance": {
                country: {
                    "models_deployed": random.randint(5, 15),
                    "avg_bias_score": round(random.uniform(0.1, 0.8), 2),
                    "compliance_status": random.choice(["COMPLIANT", "WARNING", "NON_COMPLIANT"])
                } for country in countries
            }
        }

# Create global instance
supabase_service = SupabaseService() 