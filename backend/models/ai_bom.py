"""
AI/ML Bill of Materials (BOM) Models and Analysis

This module provides comprehensive BOM management including:
- Dependency tracking and analysis
- Vulnerability detection
- License compliance checking
- Risk assessment
- BOM generation and export
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from enum import Enum
import hashlib
import json
import re
from pathlib import Path

class BOMItemType(str, Enum):
    FRAMEWORK = "framework"
    LIBRARY = "library"
    DATASET = "dataset"
    MODEL = "model"
    DEPENDENCY = "dependency"
    TOOL = "tool"
    SERVICE = "service"

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ComplianceStatus(str, Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PENDING = "pending"
    UNKNOWN = "unknown"

class LicenseType(str, Enum):
    MIT = "MIT"
    APACHE_2 = "Apache-2.0"
    BSD_3 = "BSD-3-Clause"
    GPL_3 = "GPL-3.0"
    PROPRIETARY = "Proprietary"
    CUSTOM = "Custom"
    UNKNOWN = "Unknown"

class VulnerabilitySeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class BOMItem(BaseModel):
    """Individual BOM item representing a component"""
    id: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Component name")
    version: str = Field(..., description="Component version")
    type: BOMItemType = Field(..., description="Component type")
    license: str = Field(..., description="License information")
    source: str = Field(..., description="Source URL or repository")
    size: Optional[str] = Field(None, description="Component size")
    checksum: Optional[str] = Field(None, description="SHA256 checksum")
    risk_level: RiskLevel = Field(RiskLevel.LOW, description="Risk assessment")
    compliance_status: ComplianceStatus = Field(ComplianceStatus.PENDING, description="Compliance status")
    last_updated: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    description: str = Field(..., description="Component description")
    dependencies: List[str] = Field(default_factory=list, description="Direct dependencies")
    vulnerabilities: List[Dict[str, Any]] = Field(default_factory=list, description="Security vulnerabilities")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class Vulnerability(BaseModel):
    """Security vulnerability information"""
    id: str = Field(..., description="Vulnerability ID (CVE, etc.)")
    title: str = Field(..., description="Vulnerability title")
    description: str = Field(..., description="Detailed description")
    severity: VulnerabilitySeverity = Field(..., description="Severity level")
    cvss_score: Optional[float] = Field(None, description="CVSS score")
    affected_versions: List[str] = Field(default_factory=list, description="Affected versions")
    fixed_versions: List[str] = Field(default_factory=list, description="Fixed versions")
    references: List[str] = Field(default_factory=list, description="Reference URLs")
    discovered_date: Optional[datetime] = Field(None, description="Discovery date")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class LicenseInfo(BaseModel):
    """License information and compliance"""
    name: str = Field(..., description="License name")
    type: LicenseType = Field(..., description="License type")
    url: Optional[str] = Field(None, description="License URL")
    text: Optional[str] = Field(None, description="License text")
    is_compatible: bool = Field(True, description="Compatibility with project")
    restrictions: List[str] = Field(default_factory=list, description="License restrictions")
    requirements: List[str] = Field(default_factory=list, description="License requirements")

class BOMAnalysis(BaseModel):
    """BOM analysis results"""
    total_components: int = Field(..., description="Total number of components")
    risk_distribution: Dict[RiskLevel, int] = Field(default_factory=dict, description="Risk level distribution")
    compliance_summary: Dict[ComplianceStatus, int] = Field(default_factory=dict, description="Compliance summary")
    license_distribution: Dict[str, int] = Field(default_factory=dict, description="License distribution")
    vulnerability_summary: Dict[VulnerabilitySeverity, int] = Field(default_factory=dict, description="Vulnerability summary")
    critical_issues: List[Dict[str, Any]] = Field(default_factory=list, description="Critical issues found")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations")

class BOMDocument(BaseModel):
    """Complete BOM document"""
    id: str = Field(..., description="BOM document ID")
    name: str = Field(..., description="BOM name")
    version: str = Field(..., description="BOM version")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    project_name: str = Field(..., description="Project name")
    project_version: str = Field(..., description="Project version")
    description: str = Field(..., description="Project description")
    components: List[BOMItem] = Field(default_factory=list, description="BOM components")
    analysis: Optional[BOMAnalysis] = Field(None, description="BOM analysis results")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class BOMScanRequest(BaseModel):
    """Request for BOM scanning"""
    project_path: str = Field(..., description="Path to project directory")
    scan_type: str = Field("comprehensive", description="Type of scan (comprehensive, quick, security)")
    include_dev_dependencies: bool = Field(True, description="Include development dependencies")
    include_transitive: bool = Field(True, description="Include transitive dependencies")
    output_format: str = Field("json", description="Output format (json, spdx, cyclonedx)")

class BOMScanResult(BaseModel):
    """Result of BOM scanning"""
    scan_id: str = Field(..., description="Scan ID")
    status: str = Field(..., description="Scan status")
    bom_document: Optional[BOMDocument] = Field(None, description="Generated BOM document")
    scan_errors: List[str] = Field(default_factory=list, description="Scan errors")
    scan_warnings: List[str] = Field(default_factory=list, description="Scan warnings")
    scan_duration: float = Field(..., description="Scan duration in seconds")

# Utility functions for BOM analysis
def calculate_checksum(file_path: str) -> str:
    """Calculate SHA256 checksum of a file"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def analyze_risk_level(item: BOMItem) -> RiskLevel:
    """Analyze risk level based on various factors"""
    risk_score = 0
    
    # Check for vulnerabilities
    for vuln in item.vulnerabilities:
        if vuln.get("severity") == "critical":
            risk_score += 10
        elif vuln.get("severity") == "high":
            risk_score += 7
        elif vuln.get("severity") == "medium":
            risk_score += 4
        elif vuln.get("severity") == "low":
            risk_score += 1
    
    # Check license compliance
    if item.compliance_status == ComplianceStatus.NON_COMPLIANT:
        risk_score += 5
    
    # Check for proprietary components
    if "proprietary" in item.license.lower():
        risk_score += 3
    
    # Determine risk level
    if risk_score >= 10:
        return RiskLevel.CRITICAL
    elif risk_score >= 7:
        return RiskLevel.HIGH
    elif risk_score >= 4:
        return RiskLevel.MEDIUM
    else:
        return RiskLevel.LOW

def validate_license_compatibility(license_name: str) -> ComplianceStatus:
    """Validate license compatibility"""
    compatible_licenses = [
        "MIT", "Apache-2.0", "BSD-3-Clause", "ISC", "Unlicense"
    ]
    
    restrictive_licenses = [
        "GPL-3.0", "AGPL-3.0", "LGPL-3.0"
    ]
    
    license_lower = license_name.lower()
    
    if any(comp.lower() in license_lower for comp in compatible_licenses):
        return ComplianceStatus.COMPLIANT
    elif any(rest.lower() in license_lower for rest in restrictive_licenses):
        return ComplianceStatus.NON_COMPLIANT
    else:
        return ComplianceStatus.PENDING

def generate_bom_analysis(bom_document: BOMDocument) -> BOMAnalysis:
    """Generate comprehensive BOM analysis"""
    total_components = len(bom_document.components)
    
    # Risk distribution
    risk_distribution = {}
    for item in bom_document.components:
        risk_distribution[item.risk_level] = risk_distribution.get(item.risk_level, 0) + 1
    
    # Compliance summary
    compliance_summary = {}
    for item in bom_document.components:
        compliance_summary[item.compliance_status] = compliance_summary.get(item.compliance_status, 0) + 1
    
    # License distribution
    license_distribution = {}
    for item in bom_document.components:
        license_distribution[item.license] = license_distribution.get(item.license, 0) + 1
    
    # Vulnerability summary
    vulnerability_summary = {}
    for item in bom_document.components:
        for vuln in item.vulnerabilities:
            severity = vuln.get("severity", "unknown")
            vulnerability_summary[severity] = vulnerability_summary.get(severity, 0) + 1
    
    # Critical issues
    critical_issues = []
    for item in bom_document.components:
        if item.risk_level == RiskLevel.CRITICAL:
            critical_issues.append({
                "component": item.name,
                "version": item.version,
                "issue": "Critical risk level",
                "details": f"Component {item.name} has critical risk level"
            })
        
        for vuln in item.vulnerabilities:
            if vuln.get("severity") == "critical":
                critical_issues.append({
                    "component": item.name,
                    "version": item.version,
                    "issue": "Critical vulnerability",
                    "details": vuln.get("description", "Critical security vulnerability")
                })
    
    # Recommendations
    recommendations = []
    if critical_issues:
        recommendations.append("Address critical vulnerabilities immediately")
    
    if compliance_summary.get(ComplianceStatus.NON_COMPLIANT, 0) > 0:
        recommendations.append("Review license compliance for non-compliant components")
    
    if risk_distribution.get(RiskLevel.HIGH, 0) > 0:
        recommendations.append("Consider alternatives for high-risk components")
    
    if not recommendations:
        recommendations.append("BOM appears to be in good standing")
    
    return BOMAnalysis(
        total_components=total_components,
        risk_distribution=risk_distribution,
        compliance_summary=compliance_summary,
        license_distribution=license_distribution,
        vulnerability_summary=vulnerability_summary,
        critical_issues=critical_issues,
        recommendations=recommendations
    )
