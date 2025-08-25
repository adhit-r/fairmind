"""
CycloneDX AI/ML-BOM Service

This service generates and manages CycloneDX format AI/ML Bill of Materials (AIBOM)
with comprehensive vulnerability detection and visualization capabilities.

Based on CycloneDX specification for AI/ML components:
- https://cyclonedx.org/tool-center/
- Supports AI/ML-BOM capability
- Integrates with vulnerability databases
- Provides visualization and analysis
"""

import os
import json
import hashlib
import subprocess
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging
from dataclasses import dataclass, asdict
import uuid

logger = logging.getLogger(__name__)

@dataclass
class CycloneDXComponent:
    """CycloneDX component structure for AI/ML-BOM"""
    type: str  # library, application, framework, model, dataset
    name: str
    version: str
    description: Optional[str] = None
    licenses: Optional[List[Dict[str, Any]]] = None
    externalReferences: Optional[List[Dict[str, Any]]] = None
    properties: Optional[List[Dict[str, str]]] = None
    vulnerabilities: Optional[List[Dict[str, Any]]] = None
    bomRef: Optional[str] = None
    purl: Optional[str] = None
    cpe: Optional[str] = None

@dataclass
class CycloneDXBOM:
    """Complete CycloneDX BOM structure"""
    bomFormat: str = "CycloneDX"
    specVersion: str = "1.6"
    version: int = 1
    metadata: Optional[Dict[str, Any]] = None
    components: Optional[List[Dict[str, Any]]] = None
    dependencies: Optional[List[Dict[str, Any]]] = None
    vulnerabilities: Optional[List[Dict[str, Any]]] = None

class CycloneDXAIBOMService:
    """CycloneDX AI/ML-BOM Service with vulnerability detection and visualization"""
    
    def __init__(self):
        self.vulnerability_sources = {
            "nvd": "https://services.nvd.nist.gov/rest/json/cves/2.0",
            "osv": "https://api.osv.dev/v1/query",
            "github": "https://api.github.com/advisories"
        }
        
    async def generate_aibom(self, 
                           project_path: str, 
                           organization_id: str,
                           include_vulnerabilities: bool = True) -> Dict[str, Any]:
        """
        Generate a comprehensive CycloneDX AI/ML-BOM
        
        Args:
            project_path: Path to the AI/ML project
            organization_id: Organization identifier
            include_vulnerabilities: Whether to include vulnerability scanning
            
        Returns:
            Complete CycloneDX BOM in JSON format
        """
        try:
            logger.info(f"Generating CycloneDX AIBOM for project: {project_path}")
            
            # Initialize BOM structure
            bom = CycloneDXBOM()
            
            # Set metadata
            bom.metadata = self._create_metadata(project_path, organization_id)
            
            # Scan for components
            components = await self._scan_ai_ml_components(project_path)
            bom.components = [asdict(comp) for comp in components]
            
            # Generate dependencies
            dependencies = self._generate_dependencies(components)
            bom.dependencies = dependencies
            
            # Vulnerability scanning
            if include_vulnerabilities:
                vulnerabilities = await self._scan_vulnerabilities(components)
                bom.vulnerabilities = vulnerabilities
                
                # Add vulnerability info to components
                for component in bom.components:
                    component_vulns = [v for v in vulnerabilities if v.get("affects", [{}])[0].get("ref") == component.get("bomRef")]
                    if component_vulns:
                        component["vulnerabilities"] = component_vulns
            
            return asdict(bom)
            
        except Exception as e:
            logger.error(f"Error generating CycloneDX AIBOM: {e}")
            raise
    
    def _create_metadata(self, project_path: str, organization_id: str) -> Dict[str, Any]:
        """Create BOM metadata"""
        project_name = Path(project_path).name
        
        return {
            "timestamp": datetime.now().isoformat(),
            "tools": [{
                "vendor": "Fairmind AI",
                "name": "CycloneDX AIBOM Generator",
                "version": "1.0.0"
            }],
            "component": {
                "type": "application",
                "name": project_name,
                "version": "1.0.0",
                "description": f"AI/ML project: {project_name}",
                "properties": [
                    {"name": "organization_id", "value": organization_id},
                    {"name": "project_path", "value": project_path},
                    {"name": "aibom_type", "value": "ai_ml_project"}
                ]
            }
        }
    
    async def _scan_ai_ml_components(self, project_path: str) -> List[CycloneDXComponent]:
        """Scan for AI/ML specific components"""
        components = []
        project_path = Path(project_path)
        
        # Scan for Python dependencies
        components.extend(await self._scan_python_dependencies(project_path))
        
        # Scan for ML model files
        components.extend(await self._scan_ml_models(project_path))
        
        # Scan for datasets
        components.extend(await self._scan_datasets(project_path))
        
        # Scan for configuration files
        components.extend(await self._scan_config_files(project_path))
        
        # Scan for Docker/container files
        components.extend(await self._scan_container_files(project_path))
        
        return components
    
    async def _scan_python_dependencies(self, project_path: Path) -> List[CycloneDXComponent]:
        """Scan Python dependencies"""
        components = []
        
        # Check for requirements.txt
        requirements_file = project_path / "requirements.txt"
        if requirements_file.exists():
            with open(requirements_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Parse package name and version
                        if '==' in line:
                            name, version = line.split('==', 1)
                        elif '>=' in line:
                            name, version = line.split('>=', 1)
                        elif '<=' in line:
                            name, version = line.split('<=', 1)
                        else:
                            name, version = line, "latest"
                        
                        component = CycloneDXComponent(
                            type="library",
                            name=name.strip(),
                            version=version.strip(),
                            description=f"Python dependency: {name}",
                            bomRef=f"pkg:pypi/{name}@{version}",
                            purl=f"pkg:pypi/{name}@{version}",
                            properties=[
                                {"name": "language", "value": "python"},
                                {"name": "package_manager", "value": "pip"}
                            ]
                        )
                        components.append(component)
        
        # Check for pyproject.toml
        pyproject_file = project_path / "pyproject.toml"
        if pyproject_file.exists():
            # Add pyproject.toml as a component
            component = CycloneDXComponent(
                type="application",
                name="pyproject.toml",
                version="1.0.0",
                description="Python project configuration",
                bomRef="file://pyproject.toml",
                properties=[
                    {"name": "file_type", "value": "configuration"},
                    {"name": "language", "value": "python"}
                ]
            )
            components.append(component)
        
        return components
    
    async def _scan_ml_models(self, project_path: Path) -> List[CycloneDXComponent]:
        """Scan for ML model files"""
        components = []
        model_extensions = ['.pkl', '.joblib', '.h5', '.onnx', '.pt', '.pth', '.xgb', '.lgb', '.pb']
        
        for ext in model_extensions:
            for model_file in project_path.rglob(f"*{ext}"):
                # Calculate file hash
                file_hash = self._calculate_file_hash(model_file)
                
                # Determine framework based on extension
                framework_map = {
                    '.pkl': 'scikit-learn',
                    '.joblib': 'scikit-learn',
                    '.h5': 'tensorflow',
                    '.onnx': 'onnx',
                    '.pt': 'pytorch',
                    '.pth': 'pytorch',
                    '.xgb': 'xgboost',
                    '.lgb': 'lightgbm',
                    '.pb': 'tensorflow'
                }
                
                framework = framework_map.get(ext, 'unknown')
                
                component = CycloneDXComponent(
                    type="model",
                    name=model_file.name,
                    version="1.0.0",
                    description=f"ML model file: {model_file.name}",
                    bomRef=f"file://{model_file.relative_to(project_path)}",
                    properties=[
                        {"name": "framework", "value": framework},
                        {"name": "file_extension", "value": ext},
                        {"name": "file_size", "value": str(model_file.stat().st_size)},
                        {"name": "file_hash", "value": file_hash},
                        {"name": "model_type", "value": "trained_model"}
                    ]
                )
                components.append(component)
        
        return components
    
    async def _scan_datasets(self, project_path: Path) -> List[CycloneDXComponent]:
        """Scan for dataset files"""
        components = []
        dataset_extensions = ['.csv', '.parquet', '.json', '.hdf5', '.h5', '.npz', '.pkl']
        
        for ext in dataset_extensions:
            for dataset_file in project_path.rglob(f"*{ext}"):
                # Skip if it's in a cache or temp directory
                if any(part in str(dataset_file) for part in ['__pycache__', '.git', 'node_modules', 'venv']):
                    continue
                
                file_hash = self._calculate_file_hash(dataset_file)
                
                component = CycloneDXComponent(
                    type="dataset",
                    name=dataset_file.name,
                    version="1.0.0",
                    description=f"Dataset file: {dataset_file.name}",
                    bomRef=f"file://{dataset_file.relative_to(project_path)}",
                    properties=[
                        {"name": "file_extension", "value": ext},
                        {"name": "file_size", "value": str(dataset_file.stat().st_size)},
                        {"name": "file_hash", "value": file_hash},
                        {"name": "dataset_type", "value": "data_file"}
                    ]
                )
                components.append(component)
        
        return components
    
    async def _scan_config_files(self, project_path: Path) -> List[CycloneDXComponent]:
        """Scan for configuration files"""
        components = []
        config_files = [
            "config.yaml", "config.yml", "config.json", "settings.py",
            "environment.yml", "conda-env.yml", "Dockerfile", "docker-compose.yml"
        ]
        
        for config_file in config_files:
            config_path = project_path / config_file
            if config_path.exists():
                component = CycloneDXComponent(
                    type="application",
                    name=config_file,
                    version="1.0.0",
                    description=f"Configuration file: {config_file}",
                    bomRef=f"file://{config_file}",
                    properties=[
                        {"name": "file_type", "value": "configuration"},
                        {"name": "config_category", "value": self._get_config_category(config_file)}
                    ]
                )
                components.append(component)
        
        return components
    
    async def _scan_container_files(self, project_path: Path) -> List[CycloneDXComponent]:
        """Scan for container-related files"""
        components = []
        
        # Dockerfile
        dockerfile_path = project_path / "Dockerfile"
        if dockerfile_path.exists():
            component = CycloneDXComponent(
                type="application",
                name="Dockerfile",
                version="1.0.0",
                description="Docker container definition",
                bomRef="file://Dockerfile",
                properties=[
                    {"name": "file_type", "value": "container_definition"},
                    {"name": "container_type", "value": "docker"}
                ]
            )
            components.append(component)
        
        # docker-compose files
        for compose_file in project_path.glob("docker-compose*"):
            component = CycloneDXComponent(
                type="application",
                name=compose_file.name,
                version="1.0.0",
                description=f"Docker Compose configuration: {compose_file.name}",
                bomRef=f"file://{compose_file.name}",
                properties=[
                    {"name": "file_type", "value": "container_orchestration"},
                    {"name": "container_type", "value": "docker_compose"}
                ]
            )
            components.append(component)
        
        return components
    
    def _generate_dependencies(self, components: List[CycloneDXComponent]) -> List[Dict[str, Any]]:
        """Generate dependency relationships"""
        dependencies = []
        
        # Create a dependency for the main project
        main_dep = {
            "ref": "main-project",
            "dependsOn": [comp.bomRef for comp in components if comp.bomRef]
        }
        dependencies.append(main_dep)
        
        return dependencies
    
    async def _scan_vulnerabilities(self, components: List[CycloneDXComponent]) -> List[Dict[str, Any]]:
        """Scan for vulnerabilities in components"""
        vulnerabilities = []
        
        for component in components:
            if component.type == "library" and component.purl:
                # Check NVD for vulnerabilities
                nvd_vulns = await self._check_nvd_vulnerabilities(component)
                vulnerabilities.extend(nvd_vulns)
                
                # Check OSV for vulnerabilities
                osv_vulns = await self._check_osv_vulnerabilities(component)
                vulnerabilities.extend(osv_vulns)
        
        return vulnerabilities
    
    async def _check_nvd_vulnerabilities(self, component: CycloneDXComponent) -> List[Dict[str, Any]]:
        """Check NVD database for vulnerabilities"""
        vulnerabilities = []
        
        try:
            # Extract package info from purl
            if component.purl and component.purl.startswith("pkg:pypi/"):
                package_name = component.purl.split("/")[1].split("@")[0]
                
                # Query NVD API
                url = f"{self.vulnerability_sources['nvd']}?keyword={package_name}"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    for vuln in data.get("vulnerabilities", []):
                        cve = vuln.get("cve", {})
                        vuln_id = cve.get("id")
                        
                        if vuln_id:
                            vulnerability = {
                                "id": vuln_id,
                                "source": {
                                    "name": "NVD",
                                    "url": f"https://nvd.nist.gov/vuln/detail/{vuln_id}"
                                },
                                "ratings": [
                                    {
                                        "source": {
                                            "name": "NVD"
                                        },
                                        "score": cve.get("metrics", {}).get("cvssMetricV31", [{}])[0].get("cvssData", {}).get("baseScore"),
                                        "severity": cve.get("metrics", {}).get("cvssMetricV31", [{}])[0].get("cvssData", {}).get("baseSeverity")
                                    }
                                ],
                                "description": cve.get("descriptions", [{}])[0].get("value", ""),
                                "affects": [
                                    {
                                        "ref": component.bomRef
                                    }
                                ]
                            }
                            vulnerabilities.append(vulnerability)
        
        except Exception as e:
            logger.warning(f"Error checking NVD vulnerabilities for {component.name}: {e}")
        
        return vulnerabilities
    
    async def _check_osv_vulnerabilities(self, component: CycloneDXComponent) -> List[Dict[str, Any]]:
        """Check OSV database for vulnerabilities"""
        vulnerabilities = []
        
        try:
            if component.purl and component.purl.startswith("pkg:pypi/"):
                package_name = component.purl.split("/")[1].split("@")[0]
                
                # Query OSV API
                query = {
                    "package": {
                        "name": package_name,
                        "ecosystem": "PyPI"
                    }
                }
                
                response = requests.post(self.vulnerability_sources["osv"], json=query, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    for vuln in data.get("vulns", []):
                        vulnerability = {
                            "id": vuln.get("id"),
                            "source": {
                                "name": "OSV",
                                "url": f"https://ossf.github.io/osv-schema/#{vuln.get('id')}"
                            },
                            "ratings": [
                                {
                                    "source": {
                                        "name": "OSV"
                                    },
                                    "severity": vuln.get("severity", [{}])[0].get("type", "unknown")
                                }
                            ],
                            "description": vuln.get("summary", ""),
                            "affects": [
                                {
                                    "ref": component.bomRef
                                }
                            ]
                        }
                        vulnerabilities.append(vulnerability)
        
        except Exception as e:
            logger.warning(f"Error checking OSV vulnerabilities for {component.name}: {e}")
        
        return vulnerabilities
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def _get_config_category(self, filename: str) -> str:
        """Get configuration category based on filename"""
        if filename in ["config.yaml", "config.yml", "config.json", "settings.py"]:
            return "application_config"
        elif filename in ["environment.yml", "conda-env.yml"]:
            return "environment_config"
        elif filename in ["Dockerfile", "docker-compose.yml"]:
            return "container_config"
        else:
            return "general_config"
    
    async def generate_visualization_data(self, bom_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate visualization data for the BOM"""
        components = bom_data.get("components", [])
        vulnerabilities = bom_data.get("vulnerabilities", [])
        
        # Component type distribution
        type_distribution = {}
        for comp in components:
            comp_type = comp.get("type", "unknown")
            type_distribution[comp_type] = type_distribution.get(comp_type, 0) + 1
        
        # Vulnerability severity distribution
        severity_distribution = {}
        for vuln in vulnerabilities:
            for rating in vuln.get("ratings", []):
                severity = rating.get("severity", "unknown")
                severity_distribution[severity] = severity_distribution.get(severity, 0) + 1
        
        # Framework distribution (for ML models)
        framework_distribution = {}
        for comp in components:
            if comp.get("type") == "model":
                for prop in comp.get("properties", []):
                    if prop.get("name") == "framework":
                        framework = prop.get("value", "unknown")
                        framework_distribution[framework] = framework_distribution.get(framework, 0) + 1
        
        # Risk assessment
        risk_assessment = {
            "total_components": len(components),
            "total_vulnerabilities": len(vulnerabilities),
            "critical_vulnerabilities": severity_distribution.get("CRITICAL", 0),
            "high_vulnerabilities": severity_distribution.get("HIGH", 0),
            "medium_vulnerabilities": severity_distribution.get("MEDIUM", 0),
            "low_vulnerabilities": severity_distribution.get("LOW", 0)
        }
        
        return {
            "type_distribution": type_distribution,
            "severity_distribution": severity_distribution,
            "framework_distribution": framework_distribution,
            "risk_assessment": risk_assessment,
            "components": components,
            "vulnerabilities": vulnerabilities
        }
    
    async def export_to_spdx(self, bom_data: Dict[str, Any]) -> str:
        """Export BOM to SPDX format"""
        # This would implement SPDX export
        # For now, return a placeholder
        return json.dumps({"format": "SPDX", "data": bom_data}, indent=2)
    
    async def export_to_json(self, bom_data: Dict[str, Any]) -> str:
        """Export BOM to JSON format"""
        return json.dumps(bom_data, indent=2)
    
    async def export_to_xml(self, bom_data: Dict[str, Any]) -> str:
        """Export BOM to XML format"""
        # This would implement XML export
        # For now, return a placeholder
        return f"<bom>{json.dumps(bom_data)}</bom>"

# Global instance
cyclonedx_aibom_service = CycloneDXAIBOMService()
