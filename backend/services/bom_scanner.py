"""
AI/ML Bill of Materials Scanner Service

This service provides comprehensive BOM scanning capabilities for:
- Python projects (requirements.txt, setup.py, pyproject.toml)
- Node.js projects (package.json)
- ML model files (.pkl, .joblib, .h5, .onnx)
- Dataset files (.csv, .parquet, .json)
- Docker containers
- General file systems
"""

import os
import json
import subprocess
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging
import re
import requests
from urllib.parse import urlparse

from models.ai_bom import (
    BOMItem, BOMDocument, BOMAnalysis, BOMScanResult, BOMScanRequest,
    BOMItemType, RiskLevel, ComplianceStatus, Vulnerability, LicenseInfo,
    calculate_checksum, analyze_risk_level, validate_license_compatibility,
    generate_bom_analysis
)

logger = logging.getLogger(__name__)

class BOMScanner:
    """Comprehensive BOM scanner for AI/ML projects"""
    
    def __init__(self):
        self.supported_formats = {
            'python': ['.py', '.ipynb', 'requirements.txt', 'setup.py', 'pyproject.toml'],
            'nodejs': ['package.json', 'package-lock.json', 'yarn.lock'],
            'models': ['.pkl', '.joblib', '.h5', '.onnx', '.pb', '.tflite'],
            'datasets': ['.csv', '.parquet', '.json', '.hdf5', '.npy'],
            'docker': ['Dockerfile', 'docker-compose.yml'],
            'config': ['.yaml', '.yml', '.toml', '.ini', '.cfg']
        }
        
        self.vulnerability_sources = [
            'https://api.github.com/advisories',
            'https://nvd.nist.gov/vuln/data-feeds',
            'https://pypi.org/pypi'
        ]
    
    async def scan_project(self, request: BOMScanRequest) -> BOMScanResult:
        """Scan a project and generate a comprehensive BOM"""
        start_time = datetime.now()
        scan_id = f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(request.project_path) % 10000}"
        
        try:
            logger.info(f"Starting BOM scan {scan_id} for project: {request.project_path}")
            
            # Validate project path
            if not os.path.exists(request.project_path):
                return BOMScanResult(
                    scan_id=scan_id,
                    status="failed",
                    scan_errors=[f"Project path does not exist: {request.project_path}"],
                    scan_duration=(datetime.now() - start_time).total_seconds()
                )
            
            # Scan for components based on scan type
            components = []
            scan_warnings = []
            
            if request.scan_type == "comprehensive":
                components.extend(await self._scan_python_dependencies(request.project_path))
                components.extend(await self._scan_nodejs_dependencies(request.project_path))
                components.extend(await self._scan_ml_models(request.project_path))
                components.extend(await self._scan_datasets(request.project_path))
                components.extend(await self._scan_docker_files(request.project_path))
                
            elif request.scan_type == "quick":
                components.extend(await self._scan_python_dependencies(request.project_path))
                components.extend(await self._scan_nodejs_dependencies(request.project_path))
                
            elif request.scan_type == "security":
                components.extend(await self._scan_python_dependencies(request.project_path))
                components.extend(await self._scan_nodejs_dependencies(request.project_path))
                # Add security-specific scanning
                await self._scan_vulnerabilities(components)
            
            # Generate BOM document
            bom_document = BOMDocument(
                id=f"bom_{scan_id}",
                name=f"BOM for {os.path.basename(request.project_path)}",
                version="1.0.0",
                project_name=os.path.basename(request.project_path),
                project_version="1.0.0",
                description=f"AI/ML Bill of Materials for {request.project_path}",
                components=components,
                metadata={
                    "scan_type": request.scan_type,
                    "include_dev_dependencies": request.include_dev_dependencies,
                    "include_transitive": request.include_transitive,
                    "scanned_at": datetime.now().isoformat()
                }
            )
            
            # Generate analysis
            bom_document.analysis = generate_bom_analysis(bom_document)
            
            scan_duration = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"BOM scan {scan_id} completed successfully in {scan_duration:.2f}s")
            
            return BOMScanResult(
                scan_id=scan_id,
                status="completed",
                bom_document=bom_document,
                scan_warnings=scan_warnings,
                scan_duration=scan_duration
            )
            
        except Exception as e:
            logger.error(f"BOM scan {scan_id} failed: {str(e)}")
            return BOMScanResult(
                scan_id=scan_id,
                status="failed",
                scan_errors=[f"Scan failed: {str(e)}"],
                scan_duration=(datetime.now() - start_time).total_seconds()
            )
    
    async def _scan_python_dependencies(self, project_path: str) -> List[BOMItem]:
        """Scan Python dependencies"""
        components = []
        
        # Check for requirements.txt
        requirements_file = os.path.join(project_path, "requirements.txt")
        if os.path.exists(requirements_file):
            components.extend(await self._parse_requirements_txt(requirements_file))
        
        # Check for setup.py
        setup_file = os.path.join(project_path, "setup.py")
        if os.path.exists(setup_file):
            components.extend(await self._parse_setup_py(setup_file))
        
        # Check for pyproject.toml
        pyproject_file = os.path.join(project_path, "pyproject.toml")
        if os.path.exists(pyproject_file):
            components.extend(await self._parse_pyproject_toml(pyproject_file))
        
        return components
    
    async def _parse_requirements_txt(self, file_path: str) -> List[BOMItem]:
        """Parse requirements.txt file"""
        components = []
        
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Parse package specification
                    package_info = self._parse_package_spec(line)
                    if package_info:
                        component = BOMItem(
                            id=f"python-{package_info['name']}",
                            name=package_info['name'],
                            version=package_info['version'],
                            type=BOMItemType.LIBRARY,
                            license="Unknown",  # Will be updated later
                            source=f"https://pypi.org/project/{package_info['name']}/",
                            description=f"Python package: {package_info['name']}",
                            metadata={
                                "source_file": file_path,
                                "specification": line
                            }
                        )
                        components.append(component)
        
        except Exception as e:
            logger.error(f"Error parsing requirements.txt {file_path}: {str(e)}")
        
        return components
    
    async def _parse_setup_py(self, file_path: str) -> List[BOMItem]:
        """Parse setup.py file"""
        components = []
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Extract install_requires
            install_requires_match = re.search(r'install_requires\s*=\s*\[(.*?)\]', content, re.DOTALL)
            if install_requires_match:
                requires_text = install_requires_match.group(1)
                packages = re.findall(r'["\']([^"\']+)["\']', requires_text)
                
                for package in packages:
                    package_info = self._parse_package_spec(package)
                    if package_info:
                        component = BOMItem(
                            id=f"python-{package_info['name']}",
                            name=package_info['name'],
                            version=package_info['version'],
                            type=BOMItemType.LIBRARY,
                            license="Unknown",
                            source=f"https://pypi.org/project/{package_info['name']}/",
                            description=f"Python package: {package_info['name']}",
                            metadata={
                                "source_file": file_path,
                                "specification": package
                            }
                        )
                        components.append(component)
        
        except Exception as e:
            logger.error(f"Error parsing setup.py {file_path}: {str(e)}")
        
        return components
    
    async def _parse_pyproject_toml(self, file_path: str) -> List[BOMItem]:
        """Parse pyproject.toml file"""
        components = []
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Extract dependencies from [project.dependencies]
            dependencies_match = re.search(r'\[project\.dependencies\](.*?)(?=\[|$)', content, re.DOTALL)
            if dependencies_match:
                deps_text = dependencies_match.group(1)
                lines = deps_text.strip().split('\n')
                
                for line in lines:
                    line = line.strip()
                    if '=' in line:
                        package_name = line.split('=')[0].strip().strip('"\'')
                        version_spec = line.split('=')[1].strip().strip('"\'')
                        
                        component = BOMItem(
                            id=f"python-{package_name}",
                            name=package_name,
                            version=version_spec,
                            type=BOMItemType.LIBRARY,
                            license="Unknown",
                            source=f"https://pypi.org/project/{package_name}/",
                            description=f"Python package: {package_name}",
                            metadata={
                                "source_file": file_path,
                                "specification": line
                            }
                        )
                        components.append(component)
        
        except Exception as e:
            logger.error(f"Error parsing pyproject.toml {file_path}: {str(e)}")
        
        return components
    
    async def _scan_nodejs_dependencies(self, project_path: str) -> List[BOMItem]:
        """Scan Node.js dependencies"""
        components = []
        
        package_json = os.path.join(project_path, "package.json")
        if os.path.exists(package_json):
            components.extend(await self._parse_package_json(package_json))
        
        return components
    
    async def _parse_package_json(self, file_path: str) -> List[BOMItem]:
        """Parse package.json file"""
        components = []
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Dependencies
            dependencies = data.get('dependencies', {})
            for name, version in dependencies.items():
                component = BOMItem(
                    id=f"nodejs-{name}",
                    name=name,
                    version=version,
                    type=BOMItemType.LIBRARY,
                    license="Unknown",
                    source=f"https://www.npmjs.com/package/{name}",
                    description=f"Node.js package: {name}",
                    metadata={
                        "source_file": file_path,
                        "package_type": "dependency"
                    }
                )
                components.append(component)
            
            # Dev dependencies
            dev_dependencies = data.get('devDependencies', {})
            for name, version in dev_dependencies.items():
                component = BOMItem(
                    id=f"nodejs-dev-{name}",
                    name=name,
                    version=version,
                    type=BOMItemType.LIBRARY,
                    license="Unknown",
                    source=f"https://www.npmjs.com/package/{name}",
                    description=f"Node.js dev package: {name}",
                    metadata={
                        "source_file": file_path,
                        "package_type": "devDependency"
                    }
                )
                components.append(component)
        
        except Exception as e:
            logger.error(f"Error parsing package.json {file_path}: {str(e)}")
        
        return components
    
    async def _scan_ml_models(self, project_path: str) -> List[BOMItem]:
        """Scan for ML model files"""
        components = []
        
        model_extensions = ['.pkl', '.joblib', '.h5', '.onnx', '.pb', '.tflite']
        
        for root, dirs, files in os.walk(project_path):
            for file in files:
                if any(file.endswith(ext) for ext in model_extensions):
                    file_path = os.path.join(root, file)
                    try:
                        file_size = os.path.getsize(file_path)
                        checksum = calculate_checksum(file_path)
                        
                        component = BOMItem(
                            id=f"model-{checksum[:8]}",
                            name=file,
                            version="1.0.0",
                            type=BOMItemType.MODEL,
                            license="Unknown",
                            source=file_path,
                            size=f"{file_size / (1024*1024):.2f}MB",
                            checksum=checksum,
                            description=f"ML model file: {file}",
                            metadata={
                                "file_path": file_path,
                                "file_size_bytes": file_size,
                                "model_format": Path(file).suffix
                            }
                        )
                        components.append(component)
                    
                    except Exception as e:
                        logger.error(f"Error scanning model file {file_path}: {str(e)}")
        
        return components
    
    async def _scan_datasets(self, project_path: str) -> List[BOMItem]:
        """Scan for dataset files"""
        components = []
        
        dataset_extensions = ['.csv', '.parquet', '.json', '.hdf5', '.npy']
        
        for root, dirs, files in os.walk(project_path):
            for file in files:
                if any(file.endswith(ext) for ext in dataset_extensions):
                    file_path = os.path.join(root, file)
                    try:
                        file_size = os.path.getsize(file_path)
                        checksum = calculate_checksum(file_path)
                        
                        component = BOMItem(
                            id=f"dataset-{checksum[:8]}",
                            name=file,
                            version="1.0.0",
                            type=BOMItemType.DATASET,
                            license="Unknown",
                            source=file_path,
                            size=f"{file_size / (1024*1024):.2f}MB",
                            checksum=checksum,
                            description=f"Dataset file: {file}",
                            metadata={
                                "file_path": file_path,
                                "file_size_bytes": file_size,
                                "dataset_format": Path(file).suffix
                            }
                        )
                        components.append(component)
                    
                    except Exception as e:
                        logger.error(f"Error scanning dataset file {file_path}: {str(e)}")
        
        return components
    
    async def _scan_docker_files(self, project_path: str) -> List[BOMItem]:
        """Scan Docker files"""
        components = []
        
        docker_files = ['Dockerfile', 'docker-compose.yml', 'docker-compose.yaml']
        
        for docker_file in docker_files:
            file_path = os.path.join(project_path, docker_file)
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    # Extract base images
                    base_images = re.findall(r'FROM\s+([^\s]+)', content)
                    
                    for image in base_images:
                        component = BOMItem(
                            id=f"docker-{image.replace('/', '-').replace(':', '-')}",
                            name=image,
                            version="latest",
                            type=BOMItemType.SERVICE,
                            license="Unknown",
                            source=f"https://hub.docker.com/r/{image}",
                            description=f"Docker base image: {image}",
                            metadata={
                                "source_file": file_path,
                                "docker_type": "base_image"
                            }
                        )
                        components.append(component)
                
                except Exception as e:
                    logger.error(f"Error scanning Docker file {file_path}: {str(e)}")
        
        return components
    
    async def _scan_vulnerabilities(self, components: List[BOMItem]):
        """Scan for known vulnerabilities"""
        for component in components:
            try:
                # This would integrate with vulnerability databases
                # For now, we'll add some mock vulnerabilities
                if component.type == BOMItemType.LIBRARY:
                    # Mock vulnerability check
                    if component.name in ['requests', 'urllib3']:
                        component.vulnerabilities.append({
                            "id": "CVE-2023-1234",
                            "title": "Mock vulnerability",
                            "description": "This is a mock vulnerability for demonstration",
                            "severity": "medium",
                            "cvss_score": 6.5,
                            "affected_versions": ["<2.28.0"],
                            "fixed_versions": ["2.28.0"],
                            "references": ["https://example.com/cve-2023-1234"]
                        })
                
                # Update risk level based on vulnerabilities
                component.risk_level = analyze_risk_level(component)
                
            except Exception as e:
                logger.error(f"Error scanning vulnerabilities for {component.name}: {str(e)}")
    
    def _parse_package_spec(self, spec: str) -> Optional[Dict[str, str]]:
        """Parse package specification string"""
        try:
            # Handle different package spec formats
            if '==' in spec:
                name, version = spec.split('==', 1)
            elif '>=' in spec:
                name, version = spec.split('>=', 1)
            elif '<=' in spec:
                name, version = spec.split('<=', 1)
            elif '~=' in spec:
                name, version = spec.split('~=', 1)
            else:
                name = spec
                version = "latest"
            
            return {
                "name": name.strip(),
                "version": version.strip()
            }
        except Exception:
            return None
    
    async def export_bom(self, bom_document: BOMDocument, format: str = "json") -> str:
        """Export BOM document in specified format"""
        if format.lower() == "json":
            return bom_document.json(indent=2)
        elif format.lower() == "spdx":
            return await self._export_spdx(bom_document)
        elif format.lower() == "cyclonedx":
            return await self._export_cyclonedx(bom_document)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    async def _export_spdx(self, bom_document: BOMDocument) -> str:
        """Export in SPDX format"""
        # SPDX format implementation
        spdx_content = f"""SPDXVersion: SPDX-2.2
DataLicense: CC0-1.0
SPDXID: SPDXRef-DOCUMENT
DocumentName: {bom_document.name}
DocumentNamespace: https://fairmind.ai/bom/{bom_document.id}
Creator: Organization: Fairmind AI
Created: {bom_document.created_at.strftime('%Y-%m-%dT%H:%M:%SZ')}

"""
        
        for i, component in enumerate(bom_document.components):
            spdx_content += f"""PackageName: {component.name}
SPDXID: SPDXRef-Package-{i+1}
PackageVersion: {component.version}
PackageDownloadLocation: {component.source}
PackageLicenseDeclared: {component.license}
PackageDescription: {component.description}

"""
        
        return spdx_content
    
    async def _export_cyclonedx(self, bom_document: BOMDocument) -> str:
        """Export in CycloneDX format"""
        cyclonedx = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.4",
            "version": 1,
            "metadata": {
                "timestamp": bom_document.created_at.isoformat(),
                "tools": [{
                    "vendor": "Fairmind AI",
                    "name": "BOM Scanner",
                    "version": "1.0.0"
                }]
            },
            "components": []
        }
        
        for component in bom_document.components:
            cyclonedx["components"].append({
                "type": "library",
                "name": component.name,
                "version": component.version,
                "description": component.description,
                "licenses": [{"license": {"id": component.license}}],
                "externalReferences": [{
                    "type": "website",
                    "url": component.source
                }]
            })
        
        return json.dumps(cyclonedx, indent=2)
