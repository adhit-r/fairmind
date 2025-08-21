"""
Database Service using Node.js/Prisma integration
"""

import asyncio
import json
import subprocess
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class DatabaseService:
    """Service for database operations using Prisma client"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent.parent
        
    async def _run_prisma_script(self, script_name: str, args: List[str] = None) -> Dict:
        """Run a Node.js script that uses Prisma"""
        try:
            # Path to our Prisma scripts
            script_path = self.project_root / "tools" / "scripts" / script_name
            
            if not script_path.exists():
                raise FileNotFoundError(f"Script not found: {script_path}")
            
            cmd = ["node", str(script_path)]
            if args:
                cmd.extend(args)
            
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.project_root
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                output = stdout.decode()
                # Try to find JSON in the output (might have debug messages)
                try:
                    # Look for JSON in the output
                    lines = output.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line.startswith('{') and line.endswith('}'):
                            try:
                                return json.loads(line)
                            except json.JSONDecodeError:
                                continue
                    # If no JSON found, try parsing the whole output
                    return json.loads(output)
                except json.JSONDecodeError:
                    logger.error(f"Could not parse JSON from output: {output}")
                    return {"success": False, "error": "Invalid JSON output"}
            else:
                logger.error(f"Prisma script failed: {stderr.decode()}")
                return {"success": False, "error": stderr.decode()}
                
        except Exception as e:
            logger.error(f"Error running Prisma script: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_profiles(self, limit: int = 10) -> List[Dict]:
        """Get user profiles from database"""
        try:
            result = await self._run_prisma_script("get-profiles.js", [str(limit)])
            if result.get("success"):
                return result.get("data", [])
            else:
                logger.error(f"Failed to get profiles: {result.get('error')}")
                return []
        except Exception as e:
            logger.error(f"Error getting profiles: {e}")
            return []
    
    async def get_geographic_bias_analyses(self, limit: int = 10) -> List[Dict]:
        """Get geographic bias analyses from database"""
        try:
            result = await self._run_prisma_script("get-bias-analyses.js", [str(limit)])
            if result.get("success"):
                return result.get("data", [])
            else:
                logger.error(f"Failed to get bias analyses: {result.get('error')}")
                return []
        except Exception as e:
            logger.error(f"Error getting bias analyses: {e}")
            return []
    
    async def get_audit_logs(self, limit: int = 10) -> List[Dict]:
        """Get audit logs from database"""
        try:
            result = await self._run_prisma_script("get-audit-logs.js", [str(limit)])
            if result.get("success"):
                return result.get("data", [])
            else:
                logger.error(f"Failed to get audit logs: {result.get('error')}")
                return []
        except Exception as e:
            logger.error(f"Error getting audit logs: {e}")
            return []
    
    async def get_country_performance_metrics(self, limit: int = 10) -> List[Dict]:
        """Get country performance metrics from database"""
        try:
            result = await self._run_prisma_script("get-country-metrics.js", [str(limit)])
            if result.get("success"):
                return result.get("data", [])
            else:
                logger.error(f"Failed to get country metrics: {result.get('error')}")
                return []
        except Exception as e:
            logger.error(f"Error getting country metrics: {e}")
            return []
    
    async def create_audit_log(self, audit_data: Dict) -> Dict:
        """Create a new audit log entry"""
        try:
            result = await self._run_prisma_script("create-audit-log.js", [json.dumps(audit_data)])
            if result.get("success"):
                return result.get("data", {})
            else:
                logger.error(f"Failed to create audit log: {result.get('error')}")
                return {}
        except Exception as e:
            logger.error(f"Error creating audit log: {e}")
            return {}
    
    async def get_dashboard_stats(self) -> Dict:
        """Get dashboard statistics"""
        try:
            # Get counts from different tables
            profiles = await self.get_profiles(limit=1000)
            bias_analyses = await self.get_geographic_bias_analyses(limit=1000)
            audit_logs = await self.get_audit_logs(limit=1000)
            
            # Calculate some basic stats
            stats = {
                "total_users": len(profiles),
                "total_analyses": len(bias_analyses),
                "total_audit_logs": len(audit_logs),
                "active_users": sum(1 for p in profiles if p.get("role") in ["admin", "user"]),
                "high_risk_analyses": sum(1 for a in bias_analyses if a.get("riskLevel") == "high"),
                "recent_activity": len([a for a in audit_logs if a.get("createdAt")]) if audit_logs else 0
            }
            
            return stats
        except Exception as e:
            logger.error(f"Error getting dashboard stats: {e}")
            return {
                "total_users": 0,
                "total_analyses": 0,
                "total_audit_logs": 0,
                "active_users": 0,
                "high_risk_analyses": 0,
                "recent_activity": 0
            }

# Global instance
database_service = DatabaseService()
