"""
Bias Test Result Storage Service
Stores and retrieves bias detection test results with full history tracking
"""

import os
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from supabase import create_client, Client

logger = logging.getLogger(__name__)


class BiasTestResultService:
    """Service for storing and retrieving bias test results"""
    
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        self.local_storage_path = os.getenv("TEST_RESULTS_PATH", "./uploads/test_results")
        
        # Initialize Supabase client
        if self.supabase_url and self.supabase_key:
            try:
                self.client: Client = create_client(self.supabase_url, self.supabase_key)
                self.use_supabase = True
                logger.info("Bias test result storage initialized with Supabase")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase: {e}")
                self.client = None
                self.use_supabase = False
        else:
            self.client = None
            self.use_supabase = False
            logger.info("Bias test result storage initialized with local file system")
        
        # Ensure local storage directory exists
        os.makedirs(self.local_storage_path, exist_ok=True)
    
    async def save_test_result(
        self,
        test_id: str,
        user_id: str,
        model_id: str,
        dataset_id: Optional[str],
        test_type: str,  # "ml_bias" or "llm_bias"
        results: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Save bias test result
        
        Args:
            test_id: Unique test identifier
            user_id: User who ran the test
            model_id: Model being tested
            dataset_id: Dataset used (if applicable)
            test_type: Type of bias test (ml_bias, llm_bias)
            results: Full test results including metrics
            metadata: Additional metadata (config, parameters, etc.)
        
        Returns:
            True if saved successfully
        """
        try:
            test_record = {
                "id": test_id,
                "user_id": user_id,
                "model_id": model_id,
                "dataset_id": dataset_id,
                "test_type": test_type,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "overall_risk": results.get("overall_risk"),
                "metrics_passed": results.get("metrics_passed", 0),
                "metrics_failed": results.get("metrics_failed", 0),
                "results": results,
                "summary": results.get("summary", ""),
                "recommendations": results.get("recommendations", []),
                "metadata": metadata or {},
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            if self.use_supabase:
                await self._save_supabase(test_record)
            else:
                await self._save_local(test_record)
            
            logger.info(f"Test result saved: {test_id} (type: {test_type})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save test result {test_id}: {e}")
            return False
    
    async def _save_supabase(self, test_record: Dict[str, Any]):
        """Save test result to Supabase"""
        try:
            response = self.client.table("bias_test_results").insert(test_record).execute()
            
            if hasattr(response, 'error') and response.error:
                raise Exception(f"Database insert failed: {response.error}")
            
        except Exception as e:
            logger.error(f"Supabase save error: {e}")
            raise
    
    async def _save_local(self, test_record: Dict[str, Any]):
        """Save test result to local file system"""
        try:
            # Create user directory
            user_dir = os.path.join(self.local_storage_path, test_record["user_id"])
            os.makedirs(user_dir, exist_ok=True)
            
            # Save test result
            result_path = os.path.join(user_dir, f"{test_record['id']}.json")
            with open(result_path, 'w') as f:
                json.dump(test_record, f, indent=2)
            
            logger.info(f"Test result saved locally: {result_path}")
            
        except Exception as e:
            logger.error(f"Local save error: {e}")
            raise
    
    async def get_test_result(self, test_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific test result"""
        try:
            if self.use_supabase:
                return await self._get_supabase(test_id, user_id)
            else:
                return await self._get_local(test_id, user_id)
        except Exception as e:
            logger.error(f"Failed to retrieve test result {test_id}: {e}")
            return None
    
    async def _get_supabase(self, test_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve test result from Supabase"""
        try:
            response = self.client.table("bias_test_results")\
                .select("*")\
                .eq("id", test_id)\
                .eq("user_id", user_id)\
                .execute()
            
            if response.data:
                return response.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Supabase retrieval error: {e}")
            return None
    
    async def _get_local(self, test_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve test result from local storage"""
        try:
            result_path = os.path.join(self.local_storage_path, user_id, f"{test_id}.json")
            
            if not os.path.exists(result_path):
                return None
            
            with open(result_path, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"Local retrieval error: {e}")
            return None
    
    async def list_test_results(
        self,
        user_id: str,
        model_id: Optional[str] = None,
        test_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List test results with optional filtering"""
        try:
            if self.use_supabase:
                return await self._list_supabase(user_id, model_id, test_type, limit, offset)
            else:
                return await self._list_local(user_id, model_id, test_type, limit, offset)
        except Exception as e:
            logger.error(f"Failed to list test results: {e}")
            return []
    
    async def _list_supabase(
        self,
        user_id: str,
        model_id: Optional[str],
        test_type: Optional[str],
        limit: int,
        offset: int
    ) -> List[Dict[str, Any]]:
        """List test results from Supabase"""
        try:
            query = self.client.table("bias_test_results")\
                .select("id, model_id, dataset_id, test_type, timestamp, overall_risk, metrics_passed, metrics_failed, summary")\
                .eq("user_id", user_id)\
                .order("timestamp", desc=True)\
                .range(offset, offset + limit - 1)
            
            if model_id:
                query = query.eq("model_id", model_id)
            
            if test_type:
                query = query.eq("test_type", test_type)
            
            response = query.execute()
            return response.data
            
        except Exception as e:
            logger.error(f"Supabase list error: {e}")
            return []
    
    async def _list_local(
        self,
        user_id: str,
        model_id: Optional[str],
        test_type: Optional[str],
        limit: int,
        offset: int
    ) -> List[Dict[str, Any]]:
        """List test results from local storage"""
        try:
            user_dir = os.path.join(self.local_storage_path, user_id)
            if not os.path.exists(user_dir):
                return []
            
            results = []
            for filename in os.listdir(user_dir):
                if filename.endswith('.json'):
                    with open(os.path.join(user_dir, filename), 'r') as f:
                        result = json.load(f)
                        
                        # Apply filters
                        if model_id and result.get("model_id") != model_id:
                            continue
                        if test_type and result.get("test_type") != test_type:
                            continue
                        
                        # Return summary only
                        results.append({
                            "id": result["id"],
                            "model_id": result["model_id"],
                            "dataset_id": result.get("dataset_id"),
                            "test_type": result["test_type"],
                            "timestamp": result["timestamp"],
                            "overall_risk": result["overall_risk"],
                            "metrics_passed": result["metrics_passed"],
                            "metrics_failed": result["metrics_failed"],
                            "summary": result["summary"]
                        })
            
            # Sort by timestamp descending
            results.sort(key=lambda x: x["timestamp"], reverse=True)
            
            # Apply pagination
            return results[offset:offset + limit]
            
        except Exception as e:
            logger.error(f"Local list error: {e}")
            return []
    
    async def delete_test_result(self, test_id: str, user_id: str) -> bool:
        """Delete a test result"""
        try:
            if self.use_supabase:
                self.client.table("bias_test_results")\
                    .delete()\
                    .eq("id", test_id)\
                    .eq("user_id", user_id)\
                    .execute()
            else:
                result_path = os.path.join(self.local_storage_path, user_id, f"{test_id}.json")
                if os.path.exists(result_path):
                    os.remove(result_path)
            
            logger.info(f"Test result deleted: {test_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete test result: {e}")
            return False
    
    async def get_test_statistics(self, user_id: str, model_id: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics about test results"""
        try:
            results = await self.list_test_results(user_id, model_id=model_id, limit=1000)
            
            total_tests = len(results)
            if total_tests == 0:
                return {
                    "total_tests": 0,
                    "by_risk": {},
                    "by_type": {},
                    "pass_rate": 0.0
                }
            
            by_risk = {}
            by_type = {}
            total_passed = 0
            total_failed = 0
            
            for result in results:
                # Count by risk level
                risk = result.get("overall_risk", "unknown")
                by_risk[risk] = by_risk.get(risk, 0) + 1
                
                # Count by test type
                test_type = result.get("test_type", "unknown")
                by_type[test_type] = by_type.get(test_type, 0) + 1
                
                # Count passed/failed metrics
                total_passed += result.get("metrics_passed", 0)
                total_failed += result.get("metrics_failed", 0)
            
            total_metrics = total_passed + total_failed
            pass_rate = (total_passed / total_metrics * 100) if total_metrics > 0 else 0.0
            
            return {
                "total_tests": total_tests,
                "by_risk": by_risk,
                "by_type": by_type,
                "total_metrics_tested": total_metrics,
                "metrics_passed": total_passed,
                "metrics_failed": total_failed,
                "pass_rate": round(pass_rate, 2)
            }
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}


# Global instance
bias_test_results = BiasTestResultService()
