"""
Prisma Client for Fairmind Backend
This module provides a Python interface to the Prisma database client
"""

import os
import json
import asyncio
from typing import Dict, List, Optional, Any
from pathlib import Path
import subprocess
import logging

logger = logging.getLogger(__name__)

class PrismaClient:
    """Python wrapper for Prisma client"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.prisma_schema = self.project_root / "prisma" / "schema.prisma"
        
    async def execute_query(self, query: str, variables: Dict = None) -> Dict:
        """Execute a Prisma query using the CLI"""
        try:
            # Use Prisma CLI to execute queries
            cmd = ["npx", "prisma", "db", "execute", "--stdin"]
            
            if variables:
                query_data = {
                    "query": query,
                    "variables": variables
                }
                input_data = json.dumps(query_data)
            else:
                input_data = query
                
            result = subprocess.run(
                cmd,
                input=input_data.encode(),
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                logger.error(f"Prisma query failed: {result.stderr}")
                return {"error": result.stderr}
                
        except Exception as e:
            logger.error(f"Error executing Prisma query: {e}")
            return {"error": str(e)}
    
    async def get_profiles(self, limit: int = 10) -> List[Dict]:
        """Get profiles from the database"""
        query = """
        query GetProfiles($limit: Int!) {
            profiles(take: $limit) {
                id
                username
                fullName
                avatarUrl
                role
                createdAt
                updatedAt
            }
        }
        """
        result = await self.execute_query(query, {"limit": limit})
        return result.get("data", {}).get("profiles", [])
    
    async def get_geographic_bias_analyses(self, limit: int = 10) -> List[Dict]:
        """Get geographic bias analyses from the database"""
        query = """
        query GetGeographicBiasAnalyses($limit: Int!) {
            geographicBiasAnalyses(take: $limit) {
                id
                modelId
                sourceCountry
                targetCountry
                biasScore
                riskLevel
                culturalFactors
                createdBy
                complianceStatus
                analysisDate
            }
        }
        """
        result = await self.execute_query(query, {"limit": limit})
        return result.get("data", {}).get("geographicBiasAnalyses", [])
    
    async def get_audit_logs(self, limit: int = 10) -> List[Dict]:
        """Get audit logs from the database"""
        query = """
        query GetAuditLogs($limit: Int!) {
            auditLogs(take: $limit) {
                id
                userId
                action
                resourceType
                resourceId
                details
                ipAddress
                userAgent
                createdAt
            }
        }
        """
        result = await self.execute_query(query, {"limit": limit})
        return result.get("data", {}).get("auditLogs", [])
    
    async def create_audit_log(self, audit_data: Dict) -> Dict:
        """Create a new audit log entry"""
        query = """
        mutation CreateAuditLog($data: AuditLogCreateInput!) {
            createAuditLog(data: $data) {
                id
                action
                resourceType
                resourceId
                details
                ipAddress
                userAgent
                createdAt
            }
        }
        """
        result = await self.execute_query(query, {"data": audit_data})
        return result.get("data", {}).get("createAuditLog", {})
    
    async def get_country_performance_metrics(self, limit: int = 10) -> List[Dict]:
        """Get country performance metrics from the database"""
        query = """
        query GetCountryPerformanceMetrics($limit: Int!) {
            countryPerformanceMetrics(take: $limit) {
                id
                countryCode
                countryName
                metricsData
                complianceStatus
                riskScore
                lastUpdated
            }
        }
        """
        result = await self.execute_query(query, {"limit": limit})
        return result.get("data", {}).get("countryPerformanceMetrics", [])
    
    async def get_cultural_factors(self, limit: int = 10) -> List[Dict]:
        """Get cultural factors from the database"""
        query = """
        query GetCulturalFactors($limit: Int!) {
            culturalFactors(take: $limit) {
                id
                countryCode
                factorName
                factorValue
                impactScore
                createdAt
            }
        }
        """
        result = await self.execute_query(query, {"limit": limit})
        return result.get("data", {}).get("culturalFactors", [])

# Global Prisma client instance
prisma_client = PrismaClient()

# Convenience functions for easy access
async def get_profiles(limit: int = 10) -> List[Dict]:
    """Get profiles from the database"""
    return await prisma_client.get_profiles(limit)

async def get_geographic_bias_analyses(limit: int = 10) -> List[Dict]:
    """Get geographic bias analyses from the database"""
    return await prisma_client.get_geographic_bias_analyses(limit)

async def get_audit_logs(limit: int = 10) -> List[Dict]:
    """Get audit logs from the database"""
    return await prisma_client.get_audit_logs(limit)

async def create_audit_log(audit_data: Dict) -> Dict:
    """Create a new audit log entry"""
    return await prisma_client.create_audit_log(audit_data)

async def get_country_performance_metrics(limit: int = 10) -> List[Dict]:
    """Get country performance metrics from the database"""
    return await prisma_client.get_country_performance_metrics(limit)

async def get_cultural_factors(limit: int = 10) -> List[Dict]:
    """Get cultural factors from the database"""
    return await prisma_client.get_cultural_factors(limit)
