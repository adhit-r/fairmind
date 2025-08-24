"""
AI Bill of Materials (AI BOM) Database Service - Improved Version
Database-backed service for managing and analyzing AI BOM documents with enhanced error handling,
connection management, and analysis capabilities
"""

import logging
import uuid
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass
from enum import Enum
import asyncio
from concurrent.futures import ThreadPoolExecutor

from ..models.ai_bom import (
    AIBOMDocument, AIBOMComponent, AIBOMAnalysis, AIBOMRequest,
    ComponentType, RiskLevel, ComplianceStatus,
    DataLayer, ModelDevelopmentLayer, InfrastructureLayer, DeploymentLayer,
    MonitoringLayer, SecurityLayer, ComplianceLayer
)
from ..repositories.ai_bom_repository import AIBOMRepository

logger = logging.getLogger(__name__)

class AnalysisType(Enum):
    COMPREHENSIVE = "comprehensive"
    RISK = "risk"
    COMPLIANCE = "compliance"
    SECURITY = "security"
    PERFORMANCE = "performance"
    COST = "cost"
    VULNERABILITY = "vulnerability"
    SUSTAINABILITY = "sustainability"

@dataclass
class DatabaseConfig:
    """Configuration for database connection"""
    max_retries: int = 3
    retry_delay: float = 1.0
    connection_timeout: int = 30
    query_timeout: int = 60
    organization_name: str = "FairMind"
    enable_versioning: bool = False
    enable_dependency_graphs: bool = False

class AIBOMDatabaseError(Exception):
    """Custom exception for AI BOM database operations"""
    pass

class AIBOMNotFoundError(Exception):
    """Exception for when AI BOM resources are not found"""
    pass

class AIBOMValidationError(Exception):
    """Exception for validation errors"""
    pass

class AIBOMDatabaseService:
    """Enhanced database-backed service for managing AI Bill of Materials"""
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig()
        self.repository = AIBOMRepository()
        self._is_connected = False
        self._connection_pool = None
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Keep in-memory storage as fallback when database is not available
        self.bom_documents: Dict[str, AIBOMDocument] = {}
        self.analyses: Dict[str, AIBOMAnalysis] = {}
        self._document_versions: Dict[str, List[AIBOMDocument]] = {}  # For versioning support
        
    async def initialize(self):
        """Initialize the service and establish database connection"""
        try:
            # Load existing data from persistence
            await self._load_from_persistence()
            logger.info("AI BOM Database Service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize AI BOM Database Service: {e}")
            raise AIBOMDatabaseError(f"Service initialization failed: {e}")
    
    async def shutdown(self):
        """Cleanup resources"""
        try:
            await self._save_to_persistence()
            self.executor.shutdown(wait=True)
            logger.info("AI BOM Database Service shut down successfully")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    @asynccontextmanager
    async def _database_connection(self):
        """Context manager for database connections with retry logic"""
        retries = 0
        while retries < self.config.max_retries:
            try:
                if not self._is_connected:
                    await self._connect()
                yield self
                break
            except Exception as e:
                retries += 1
                if retries >= self.config.max_retries:
                    raise AIBOMDatabaseError(f"Database connection failed after {retries} attempts: {e}")
                logger.warning(f"Database connection attempt {retries} failed: {e}. Retrying in {self.config.retry_delay}s")
                await asyncio.sleep(self.config.retry_delay)
                await self._disconnect()
    
    async def _connect(self):
        """Connect to the database with timeout"""
        try:
            # Simulate database connection for now
            await asyncio.sleep(0.1)  # Simulate connection time
            self._is_connected = True
        except Exception as e:
            self._is_connected = False
            raise AIBOMDatabaseError(f"Failed to connect to database: {e}")
    
    async def _disconnect(self):
        """Disconnect from the database"""
        try:
            if self._is_connected:
                # Simulate disconnection
                await asyncio.sleep(0.1)
                self._is_connected = False
        except Exception as e:
            logger.error(f"Failed to disconnect from database: {e}")
    
    async def create_bom_document(self, request: AIBOMRequest) -> AIBOMDocument:
        """Create a new AI BOM document with enhanced validation"""
        try:
            # Validate request
            self._validate_bom_request(request)
            
            async with self._database_connection() as db:
                # Try to use database repository first
                try:
                    if self.repository.supabase.is_connected():
                        logger.info("Creating BOM document in database")
                        document = await self.repository.create_bom_document(request)
                        
                        # Store in cache as well
                        self.bom_documents[document.id] = document
                        
                        # Store version if versioning is enabled
                        if self.config.enable_versioning:
                            if document.id not in self._document_versions:
                                self._document_versions[document.id] = []
                            self._document_versions[document.id].append(document)
                        
                        logger.info(f"AI BOM document created successfully in database: {document.id}")
                        return document
                    else:
                        raise Exception("Database not connected, falling back to in-memory storage")
                        
                except Exception as db_error:
                    logger.warning(f"Database creation failed: {db_error}, using in-memory fallback")
                    
                    # Fallback to in-memory creation
                    # Calculate metrics
                    overall_risk = self._calculate_overall_risk(request.components)
                    overall_compliance = self._calculate_overall_compliance(request.components)
                    
                    # Create layer components
                    layers = await self._create_all_layers(request.components)
                    
                    # Generate unique ID
                    bom_id = str(uuid.uuid4())
                    
                    # Create BOM document
                    bom_document = AIBOMDocument(
                        id=bom_id,
                        name=f"AI BOM - {request.project_name}",
                        version=request.version or "1.0.0",
                        description=request.description,
                        project_name=request.project_name,
                        organization=request.organization or self.config.organization_name,
                        
                        # Layer components
                        data_layer=layers['data'],
                        model_development_layer=layers['modelDevelopment'],
                        infrastructure_layer=layers['infrastructure'],
                        deployment_layer=layers['deployment'],
                    monitoring_layer=layers['monitoring'],
                    security_layer=layers['security'],
                    compliance_layer=layers['compliance'],
                    
                    # Overall assessment
                    overall_risk_level=overall_risk,
                    overall_compliance_status=overall_compliance,
                    total_components=len(request.components),
                    
                    # Metadata
                    created_by=request.created_by or "system",
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    tags=self._generate_tags(request),
                    
                    # Risk assessment
                    risk_assessment=self._generate_risk_assessment(request.components),
                    compliance_report=self._generate_compliance_report(request.components),
                    recommendations=self._generate_recommendations(request.components),
                    
                    # Components
                    components=request.components,
                    analyses=[]
                )
                
                # Store in memory and persistence
                self.bom_documents[bom_id] = bom_document
                
                # Store version if versioning is enabled
                if self.config.enable_versioning:
                    if bom_id not in self._document_versions:
                        self._document_versions[bom_id] = []
                    self._document_versions[bom_id].append(bom_document)
                
                await self._save_to_persistence()
                
                logger.info(f"Created AI BOM document: {bom_id} for project: {request.project_name}")
                
                return bom_document
                
        except Exception as e:
            logger.error(f"Error creating AI BOM document: {e}")
            raise AIBOMDatabaseError(f"Failed to create BOM document: {e}")
    
    async def list_bom_documents(self, 
                                skip: Optional[int] = 0, 
                                limit: Optional[int] = 10,
                                project_name: Optional[str] = None,
                                risk_level: Optional[str] = None,
                                compliance_status: Optional[str] = None) -> List[AIBOMDocument]:
        """List AI BOM documents with pagination and filtering"""
        try:
            async with self._database_connection() as db:
                # Try to use database repository first
                try:
                    if self.repository.supabase.is_connected():
                        logger.info("Listing BOM documents from database")
                        documents = await self.repository.list_bom_documents(
                            skip=skip or 0,
                            limit=limit or 10,
                            project_name=project_name,
                            risk_level=risk_level,
                            compliance_status=compliance_status
                        )
                        
                        # Update cache
                        for doc in documents:
                            self.bom_documents[doc.id] = doc
                        
                        logger.info(f"Retrieved {len(documents)} documents from database")
                        return documents
                    else:
                        raise Exception("Database not connected, falling back to in-memory storage")
                        
                except Exception as db_error:
                    logger.warning(f"Database listing failed: {db_error}, using in-memory fallback")
                    
                    # Fallback to in-memory listing
                    documents = list(self.bom_documents.values())
                    
                    # Apply filters
                    if project_name:
                        documents = [d for d in documents if project_name.lower() in d.project_name.lower()]
                    if risk_level:
                        documents = [d for d in documents if d.overall_risk_level.value == risk_level]
                    if compliance_status:
                        documents = [d for d in documents if d.overall_compliance_status.value == compliance_status]
                    
                    # Sort by creation date (newest first)
                    documents.sort(key=lambda x: x.created_at, reverse=True)
                    
                    # Apply pagination
                    if skip:
                        documents = documents[skip:]
                    if limit:
                        documents = documents[:limit]
                
                return documents
                
        except Exception as e:
            logger.error(f"Error listing AI BOM documents: {e}")
            raise AIBOMDatabaseError(f"Failed to list BOM documents: {e}")
    
    async def get_bom_document(self, bom_id: str) -> Optional[AIBOMDocument]:
        """Get a specific AI BOM document by ID with enhanced error handling"""
        try:
            # Validate UUID format
            uuid.UUID(bom_id)
            
            async with self._database_connection() as db:
                # Try to use database repository first
                try:
                    if self.repository.supabase.is_connected():
                        logger.info(f"Getting BOM document from database: {bom_id}")
                        document = await self.repository.get_bom_document(bom_id)
                        
                        if document:
                            # Update cache
                            self.bom_documents[document.id] = document
                            logger.info(f"Retrieved document from database: {document.project_name}")
                            return document
                        else:
                            logger.warning(f"BOM document not found in database: {bom_id}")
                            return None
                    else:
                        raise Exception("Database not connected, falling back to in-memory storage")
                        
                except Exception as db_error:
                    logger.warning(f"Database get failed: {db_error}, using in-memory fallback")
                    
                    # Fallback to in-memory storage
                    document = self.bom_documents.get(bom_id)
                    
                    if not document:
                        logger.warning(f"BOM document not found: {bom_id}")
                        return None
                    
                    return document
                
        except ValueError:
            raise AIBOMDatabaseError(f"Invalid BOM ID format: {bom_id}")
        except Exception as e:
            logger.error(f"Error retrieving AI BOM document {bom_id}: {e}")
            raise AIBOMDatabaseError(f"Failed to retrieve BOM document: {e}")
    
    async def analyze_bom(self, bom_id: str, analysis_type: Union[str, AnalysisType] = AnalysisType.COMPREHENSIVE) -> AIBOMAnalysis:
        """Analyze an AI BOM document with improved type safety and async analysis"""
        try:
            # Convert string to enum if needed
            if isinstance(analysis_type, str):
                analysis_type = AnalysisType(analysis_type)
            
            async with self._database_connection() as db:
                # Get the BOM document
                bom_doc = await self.get_bom_document(bom_id)
                if not bom_doc:
                    raise AIBOMNotFoundError(f"BOM document not found: {bom_id}")
                
                # Perform analysis asynchronously
                analysis = await self._perform_analysis(bom_doc, analysis_type)
                
                # Store analysis
                self.analyses[analysis.id] = analysis
                await self._save_to_persistence()
                
                logger.info(f"Created AI BOM analysis: {analysis.id} for document: {bom_id}")
                
                return analysis
                
        except AIBOMNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error analyzing AI BOM {bom_id}: {e}")
            raise AIBOMDatabaseError(f"Failed to analyze BOM: {e}")
    
    async def get_analysis(self, analysis_id: str) -> Optional[AIBOMAnalysis]:
        """Get a specific AI BOM analysis by ID"""
        try:
            uuid.UUID(analysis_id)  # Validate format
            
            analysis = self.analyses.get(analysis_id)
            
            if not analysis:
                return None
            
            return analysis
            
        except ValueError:
            raise AIBOMDatabaseError(f"Invalid analysis ID format: {analysis_id}")
        except Exception as e:
            logger.error(f"Error retrieving AI BOM analysis {analysis_id}: {e}")
            raise AIBOMDatabaseError(f"Failed to retrieve analysis: {e}")
    
    async def delete_bom_document(self, bom_id: str) -> bool:
        """Delete an AI BOM document and its associated analyses"""
        try:
            uuid.UUID(bom_id)  # Validate format
            
            async with self._database_connection() as db:
                # Try to use database repository first
                try:
                    if self.repository.supabase.is_connected():
                        logger.info(f"Deleting BOM document from database: {bom_id}")
                        success = await self.repository.delete_bom_document(bom_id)
                        
                        if success:
                            # Also remove from cache
                            if bom_id in self.bom_documents:
                                del self.bom_documents[bom_id]
                            
                            # Remove from versions
                            if bom_id in self._document_versions:
                                del self._document_versions[bom_id]
                            
                            # Delete associated analyses from cache
                            analyses_to_delete = [
                                analysis_id for analysis_id, analysis in self.analyses.items()
                                if hasattr(analysis, 'bom_id') and analysis.bom_id == bom_id  # Handle potential missing attribute
                            ]
                            for analysis_id in analyses_to_delete:
                                del self.analyses[analysis_id]
                            
                            logger.info(f"Successfully deleted BOM document from database: {bom_id}")
                            return True
                        else:
                            raise AIBOMNotFoundError(f"BOM document not found in database: {bom_id}")
                    else:
                        raise Exception("Database not connected, falling back to in-memory storage")
                        
                except Exception as db_error:
                    logger.warning(f"Database delete failed: {db_error}, using in-memory fallback")
                    
                    # Fallback to in-memory deletion
                    if bom_id not in self.bom_documents:
                        raise AIBOMNotFoundError(f"BOM document not found: {bom_id}")
                    
                    # Delete associated analyses
                    analyses_to_delete = [
                        analysis_id for analysis_id, analysis in self.analyses.items()
                if analysis.bom_id == bom_id
            ]
            
            for analysis_id in analyses_to_delete:
                del self.analyses[analysis_id]
            
            # Delete the document
            del self.bom_documents[bom_id]
            
            await self._save_to_persistence()
            
            logger.info(f"Deleted AI BOM document: {bom_id} and {len(analyses_to_delete)} analyses")
            return True
            
        except AIBOMNotFoundError:
            raise
        except ValueError:
            raise AIBOMDatabaseError(f"Invalid BOM ID format: {bom_id}")
        except Exception as e:
            logger.error(f"Error deleting AI BOM document {bom_id}: {e}")
            raise AIBOMDatabaseError(f"Failed to delete BOM document: {e}")
    
    async def update_bom_document(self, bom_id: str, request: AIBOMRequest) -> AIBOMDocument:
        """Update an AI BOM document"""
        try:
            uuid.UUID(bom_id)  # Validate format
            
            async with self._database_connection() as db:
                # Try to use database repository first
                try:
                    if self.repository.supabase.is_connected():
                        logger.info(f"Updating BOM document in database: {bom_id}")
                        document = await self.repository.update_bom_document(bom_id, request)
                        
                        # Update cache
                        self.bom_documents[document.id] = document
                        
                        # Store version if versioning is enabled
                        if self.config.enable_versioning:
                            if bom_id not in self._document_versions:
                                self._document_versions[bom_id] = []
                            self._document_versions[bom_id].append(document)
                        
                        logger.info(f"Successfully updated BOM document in database: {bom_id}")
                        return document
                    else:
                        raise Exception("Database not connected, falling back to in-memory storage")
                        
                except Exception as db_error:
                    logger.warning(f"Database update failed: {db_error}, using in-memory fallback")
                    
                    # Fallback to in-memory update
                    if bom_id not in self.bom_documents:
                        raise AIBOMNotFoundError(f"BOM document not found: {bom_id}")
                    
                    document = self.bom_documents[bom_id]
                    
                    # Store version if versioning is enabled
                    if self.config.enable_versioning:
                        if bom_id not in self._document_versions:
                            self._document_versions[bom_id] = []
                        self._document_versions[bom_id].append(document)
                    
                    # Apply updates from request
                    document.version = request.version or document.version
                    document.description = request.description
                    document.project_name = request.project_name
                    document.organization = request.organization or self.config.organization_name
                    document.components = request.components
                    
                    # Update timestamp
                    document.updated_at = datetime.now()
                    
                    # Recalculate metrics
                    document.overall_risk_level = self._calculate_overall_risk(document.components)
                    document.overall_compliance_status = self._calculate_overall_compliance(document.components)
                    document.total_components = len(document.components)
                    document.risk_assessment = self._generate_risk_assessment(document.components)
                    document.compliance_report = self._generate_compliance_report(document.components)
                    document.recommendations = self._generate_recommendations(document.components)
                
                await self._save_to_persistence()
                
                logger.info(f"Updated AI BOM document: {bom_id}")
                return document
                
        except AIBOMNotFoundError:
            raise
        except ValueError:
            raise AIBOMDatabaseError(f"Invalid BOM ID format: {bom_id}")
        except Exception as e:
            logger.error(f"Error updating AI BOM document {bom_id}: {e}")
            raise AIBOMDatabaseError(f"Failed to update BOM document: {e}")
    
    async def get_document_versions(self, bom_id: str) -> List[AIBOMDocument]:
        """Get all versions of a BOM document"""
        try:
            uuid.UUID(bom_id)  # Validate format
            
            if not self.config.enable_versioning:
                raise AIBOMDatabaseError("Versioning is not enabled")
            
            if bom_id not in self._document_versions:
                return []
            
            return self._document_versions[bom_id]
            
        except ValueError:
            raise AIBOMDatabaseError(f"Invalid BOM ID format: {bom_id}")
        except Exception as e:
            logger.error(f"Error retrieving document versions for {bom_id}: {e}")
            raise AIBOMDatabaseError(f"Failed to retrieve document versions: {e}")
    
    def generate_dependency_graph(self, bom_doc: AIBOMDocument) -> Dict[str, Any]:
        """Generate dependency graph for BOM components"""
        if not self.config.enable_dependency_graphs:
            raise AIBOMDatabaseError("Dependency graphs are not enabled")
        
        graph = {
            "nodes": [],
            "edges": [],
            "metadata": {
                "total_components": len(bom_doc.components),
                "total_dependencies": 0
            }
        }
        
        # Add nodes for each component
        for component in bom_doc.components:
            graph["nodes"].append({
                "id": component.id,
                "name": component.name,
                "type": component.type.value,
                "version": component.version,
                "risk_level": component.risk_level.value,
                "compliance_status": component.compliance_status.value
            })
            
            # Add edges for dependencies
            if component.dependencies:
                for dep in component.dependencies:
                    graph["edges"].append({
                        "source": component.id,
                        "target": dep,
                        "type": "depends_on"
                    })
                    graph["metadata"]["total_dependencies"] += 1
        
        return graph
    
    def export_to_cyclonedx(self, bom_doc: AIBOMDocument) -> Dict[str, Any]:
        """Export AI BOM document to CycloneDX format with enhanced metadata"""
        # Calculate package verification code
        package_verification_code = self._calculate_package_verification_code(bom_doc.components)
        
        cyclonedx_bom = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.5",
            "version": 1,
            "serialNumber": f"urn:uuid:{uuid.uuid4()}",
            "metadata": {
                "timestamp": bom_doc.created_at.isoformat() + "Z",
                "tools": [
                    {
                        "vendor": self.config.organization_name,
                        "name": "AI BOM Generator",
                        "version": "2.0.0",
                        "hashes": [
                            {
                                "alg": "SHA-256",
                                "content": package_verification_code
                            }
                        ]
                    }
                ],
                "component": {
                    "type": "application",
                    "bom-ref": f"pkg:ai/{bom_doc.project_name}@{bom_doc.version}",
                    "name": bom_doc.project_name,
                    "version": bom_doc.version,
                    "description": bom_doc.description,
                    "properties": [
                        {"name": "ai-bom:risk-level", "value": bom_doc.overall_risk_level.value},
                        {"name": "ai-bom:compliance-status", "value": bom_doc.overall_compliance_status.value},
                        {"name": "ai-bom:total-components", "value": str(bom_doc.total_components)},
                        {"name": "ai-bom:organization", "value": bom_doc.organization}
                    ]
                }
            },
            "components": []
        }
        
        # Convert components to CycloneDX format with proper UUIDs
        for component in bom_doc.components:
            component_uuid = str(uuid.uuid4())
            cyclonedx_component = {
                "type": self._map_component_type_to_cyclonedx(component.type),
                "bom-ref": component_uuid,
                "name": component.name,
                "version": component.version,
                "description": component.description,
                "properties": [
                    {"name": "ai-bom:component-type", "value": component.type.value},
                    {"name": "ai-bom:risk-level", "value": component.risk_level.value},
                    {"name": "ai-bom:compliance-status", "value": component.compliance_status.value}
                ]
            }
            
            if component.vendor:
                cyclonedx_component["supplier"] = {"name": component.vendor}
            if component.license:
                cyclonedx_component["licenses"] = [{"license": {"id": component.license}}]
            if component.dependencies:
                cyclonedx_component["dependencies"] = [
                    {"ref": f"pkg:ai/{dep}@latest"} for dep in component.dependencies
                ]
            
            cyclonedx_bom["components"].append(cyclonedx_component)
        
        return cyclonedx_bom
    
    def export_to_spdx(self, bom_doc: AIBOMDocument) -> Dict[str, Any]:
        """Export AI BOM document to SPDX format with enhanced metadata"""
        # Calculate package verification code
        package_verification_code = self._calculate_package_verification_code(bom_doc.components)
        
        spdx_document = {
            "SPDXID": "SPDXRef-DOCUMENT",
            "spdxVersion": "SPDX-2.3",
            "creationInfo": {
                "creators": [f"Tool: {self.config.organization_name} AI BOM Generator-2.0.0"],
                "created": bom_doc.created_at.isoformat() + "Z",
                "licenseListVersion": "3.21"
            },
            "name": f"{bom_doc.project_name} AI BOM",
            "dataLicense": "CC0-1.0",
            "documentNamespace": f"https://{self.config.organization_name.lower()}.ai/ai-bom/{bom_doc.id}",
            "packages": [],
            "relationships": []
        }
        
        # Add root package
        root_package = {
            "SPDXID": "SPDXRef-RootPackage",
            "name": bom_doc.project_name,
            "versionInfo": bom_doc.version,
            "description": bom_doc.description,
            "filesAnalyzed": False,
            "licenseConcluded": "NOASSERTION",
            "licenseDeclared": "NOASSERTION",
            "copyrightText": "NOASSERTION"
        }
        spdx_document["packages"].append(root_package)
        
        # Convert components to SPDX format
        for i, component in enumerate(bom_doc.components):
            spdx_id = f"SPDXRef-Component-{i}"
            spdx_package = {
                "SPDXID": spdx_id,
                "name": component.name,
                "versionInfo": component.version,
                "description": component.description,
                "filesAnalyzed": False,
                "licenseConcluded": component.license or "NOASSERTION",
                "licenseDeclared": component.license or "NOASSERTION",
                "copyrightText": "NOASSERTION",
                "supplier": component.vendor or "NOASSERTION"
            }
            spdx_document["packages"].append(spdx_package)
            
            # Add relationship to root package
            spdx_document["relationships"].append({
                "spdxElementId": "SPDXRef-RootPackage",
                "relationshipType": "DEPENDS_ON",
                "relatedSpdxElement": spdx_id
            })
        
        return spdx_document
    
    # Enhanced helper methods
    
    def _validate_bom_request(self, request: AIBOMRequest):
        """Validate BOM request data"""
        if not request.project_name:
            raise AIBOMValidationError("Project name is required")
        if not request.components:
            raise AIBOMValidationError("At least one component is required")
        
        # Validate components
        for comp in request.components:
            if not comp.name:
                raise AIBOMValidationError("Component name is required")
            if not comp.version:
                raise AIBOMValidationError("Component version is required")
            if not comp.type:
                raise AIBOMValidationError("Component type is required")
            if not comp.risk_level:
                raise AIBOMValidationError("Component risk level is required")
            if not comp.compliance_status:
                raise AIBOMValidationError("Component compliance status is required")
    
    def _generate_tags(self, request: AIBOMRequest) -> List[str]:
        """Generate tags for the BOM document"""
        tags = ["ai-bom", self.config.organization_name.lower()]
        
        if request.project_name:
            tags.append(request.project_name.lower().replace(" ", "-"))
        
        if request.organization:
            tags.append(request.organization.lower().replace(" ", "-"))
        
        # Add component type tags
        component_types = set(comp.type.value for comp in request.components)
        tags.extend(f"has-{comp_type}" for comp_type in component_types)
        
        return tags
    
    def _apply_filters(self, documents: List[AIBOMDocument], filters: Dict[str, Any]) -> List[AIBOMDocument]:
        """Apply filters to documents"""
        filtered = documents
        
        if 'project_name' in filters:
            project_name = filters['project_name'].lower()
            filtered = [doc for doc in filtered if project_name in doc.project_name.lower()]
        
        if 'risk_level' in filters:
            filtered = [doc for doc in filtered if doc.overall_risk_level == filters['risk_level']]
        
        if 'compliance_status' in filters:
            filtered = [doc for doc in filtered if doc.overall_compliance_status == filters['compliance_status']]
        
        if 'organization' in filters:
            org = filters['organization'].lower()
            filtered = [doc for doc in filtered if org in doc.organization.lower()]
        
        if 'created_after' in filters:
            filtered = [doc for doc in filtered if doc.created_at >= filters['created_after']]
        
        return filtered
    
    def _map_component_type_to_cyclonedx(self, component_type: ComponentType) -> str:
        """Map AI BOM component type to CycloneDX type"""
        mapping = {
            ComponentType.MODEL: "machine-learning-model",
            ComponentType.DATA: "data",
            ComponentType.FRAMEWORK: "framework",
            ComponentType.INFRASTRUCTURE: "platform",
            ComponentType.DEPLOYMENT: "container",
            ComponentType.MONITORING: "application",
            ComponentType.SECURITY: "library",
            ComponentType.COMPLIANCE: "library"
        }
        return mapping.get(component_type, "library")
    
    def _calculate_package_verification_code(self, components: List[AIBOMComponent]) -> str:
        """Calculate SHA1 hash over component metadata for package verification code"""
        if not components:
            return hashlib.sha1(b"").hexdigest()
        
        # Create a string representation of component metadata
        metadata_string = ""
        for comp in sorted(components, key=lambda x: x.name):
            metadata_string += f"{comp.name}:{comp.version}:{comp.type.value}:{comp.risk_level.value}:{comp.compliance_status.value}"
        
        return hashlib.sha1(metadata_string.encode()).hexdigest()
    
    async def _create_all_layers(self, components: List[AIBOMComponent]) -> Dict[str, Any]:
        """Create all layers asynchronously"""
        tasks = {
            'data': self._create_data_layer(components),
            'modelDevelopment': self._create_model_development_layer(components),
            'infrastructure': self._create_infrastructure_layer(components),
            'deployment': self._create_deployment_layer(components),
            'monitoring': self._create_monitoring_layer(components),
            'security': self._create_security_layer(components),
            'compliance': self._create_compliance_layer(components)
        }
        
        # Run layer creation concurrently
        results = await asyncio.gather(*[
            asyncio.create_task(task) for task in tasks.values()
        ])
        
        return dict(zip(tasks.keys(), results))
    
    async def _perform_analysis(self, bom_doc: AIBOMDocument, analysis_type: AnalysisType) -> AIBOMAnalysis:
        """Perform analysis based on type with async execution"""
        analysis_methods = {
            AnalysisType.COMPREHENSIVE: self._perform_comprehensive_analysis,
            AnalysisType.RISK: self._perform_risk_analysis,
            AnalysisType.COMPLIANCE: self._perform_compliance_analysis,
            AnalysisType.SECURITY: self._perform_security_analysis,
            AnalysisType.PERFORMANCE: self._perform_performance_analysis,
            AnalysisType.COST: self._perform_cost_analysis,
            AnalysisType.VULNERABILITY: self._perform_vulnerability_analysis,
            AnalysisType.SUSTAINABILITY: self._perform_sustainability_analysis
        }
        
        method = analysis_methods.get(analysis_type)
        if not method:
            raise AIBOMDatabaseError(f"Unknown analysis type: {analysis_type}")
        
        # Run analysis in executor to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, method, bom_doc)
    
    # Persistence methods (simplified for now)
    async def _load_from_persistence(self):
        """Load data from persistence layer"""
        # For now, this is a placeholder
        # In a full implementation, this would load from database or file
        logger.info("Loading AI BOM data from persistence")
    
    async def _save_to_persistence(self):
        """Save data to persistence layer"""
        # For now, this is a placeholder
        # In a full implementation, this would save to database or file
        logger.info(f"Saving {len(self.bom_documents)} BOM documents and {len(self.analyses)} analyses to persistence")
    
    # Enhanced risk and compliance calculation methods
    
    def _calculate_overall_risk(self, components: List[AIBOMComponent]) -> RiskLevel:
        """Calculate overall risk level based on component risks with weighted scoring"""
        if not components:
            return RiskLevel.LOW
        
        risk_weights = {
            RiskLevel.LOW: 1,
            RiskLevel.MEDIUM: 2,
            RiskLevel.HIGH: 3,
            RiskLevel.CRITICAL: 4
        }
        
        weighted_sum = sum(risk_weights[comp.risk_level] for comp in components)
        avg_score = weighted_sum / len(components)
        
        if avg_score >= 3.5:
            return RiskLevel.CRITICAL
        elif avg_score >= 2.5:
            return RiskLevel.HIGH
        elif avg_score >= 1.5:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _calculate_overall_compliance(self, components: List[AIBOMComponent]) -> ComplianceStatus:
        """Calculate overall compliance status based on component compliance with percentage-based logic"""
        if not components:
            return ComplianceStatus.COMPLIANT
        
        status_counts = {status: 0 for status in ComplianceStatus}
        for comp in components:
            status_counts[comp.compliance_status] += 1
        
        total = len(components)
        
        # If more than 20% are non-compliant, overall status is non-compliant
        if status_counts[ComplianceStatus.NON_COMPLIANT] / total > 0.2:
            return ComplianceStatus.NON_COMPLIANT
        # If any require review or some are non-compliant, review is required
        elif (status_counts[ComplianceStatus.REVIEW_REQUIRED] + 
              status_counts[ComplianceStatus.NON_COMPLIANT]) > 0:
            return ComplianceStatus.REVIEW_REQUIRED
        # If some are pending, overall is pending
        elif status_counts[ComplianceStatus.PENDING] > 0:
            return ComplianceStatus.PENDING
        else:
            return ComplianceStatus.COMPLIANT
    
    # Layer creation methods (simplified for now)
    async def _create_data_layer(self, components: List[AIBOMComponent]) -> DataLayer:
        """Create data layer from components"""
        data_components = [comp for comp in components if comp.type == ComponentType.DATA]
        return DataLayer(
            components=data_components,
            total_components=len(data_components),
            risk_level=self._calculate_overall_risk(data_components) if data_components else RiskLevel.LOW,
            compliance_status=self._calculate_overall_compliance(data_components) if data_components else ComplianceStatus.COMPLIANT
        )
    
    async def _create_model_development_layer(self, components: List[AIBOMComponent]) -> ModelDevelopmentLayer:
        """Create model development layer from components"""
        model_components = [comp for comp in components if comp.type == ComponentType.MODEL]
        return ModelDevelopmentLayer(
            components=model_components,
            total_components=len(model_components),
            risk_level=self._calculate_overall_risk(model_components) if model_components else RiskLevel.LOW,
            compliance_status=self._calculate_overall_compliance(model_components) if model_components else ComplianceStatus.COMPLIANT
        )
    
    async def _create_infrastructure_layer(self, components: List[AIBOMComponent]) -> InfrastructureLayer:
        """Create infrastructure layer from components"""
        infra_components = [comp for comp in components if comp.type == ComponentType.INFRASTRUCTURE]
        return InfrastructureLayer(
            components=infra_components,
            total_components=len(infra_components),
            risk_level=self._calculate_overall_risk(infra_components) if infra_components else RiskLevel.LOW,
            compliance_status=self._calculate_overall_compliance(infra_components) if infra_components else ComplianceStatus.COMPLIANT
        )
    
    async def _create_deployment_layer(self, components: List[AIBOMComponent]) -> DeploymentLayer:
        """Create deployment layer from components"""
        deploy_components = [comp for comp in components if comp.type == ComponentType.DEPLOYMENT]
        return DeploymentLayer(
            components=deploy_components,
            total_components=len(deploy_components),
            risk_level=self._calculate_overall_risk(deploy_components) if deploy_components else RiskLevel.LOW,
            compliance_status=self._calculate_overall_compliance(deploy_components) if deploy_components else ComplianceStatus.COMPLIANT
        )
    
    async def _create_monitoring_layer(self, components: List[AIBOMComponent]) -> MonitoringLayer:
        """Create monitoring layer from components"""
        monitor_components = [comp for comp in components if comp.type == ComponentType.MONITORING]
        return MonitoringLayer(
            components=monitor_components,
            total_components=len(monitor_components),
            risk_level=self._calculate_overall_risk(monitor_components) if monitor_components else RiskLevel.LOW,
            compliance_status=self._calculate_overall_compliance(monitor_components) if monitor_components else ComplianceStatus.COMPLIANT
        )
    
    async def _create_security_layer(self, components: List[AIBOMComponent]) -> SecurityLayer:
        """Create security layer from components"""
        security_components = [comp for comp in components if comp.type == ComponentType.SECURITY]
        return SecurityLayer(
            components=security_components,
            total_components=len(security_components),
            risk_level=self._calculate_overall_risk(security_components) if security_components else RiskLevel.LOW,
            compliance_status=self._calculate_overall_compliance(security_components) if security_components else ComplianceStatus.COMPLIANT
        )
    
    async def _create_compliance_layer(self, components: List[AIBOMComponent]) -> ComplianceLayer:
        """Create compliance layer from components"""
        compliance_components = [comp for comp in components if comp.type == ComponentType.COMPLIANCE]
        return ComplianceLayer(
            components=compliance_components,
            total_components=len(compliance_components),
            risk_level=self._calculate_overall_risk(compliance_components) if compliance_components else RiskLevel.LOW,
            compliance_status=self._calculate_overall_compliance(compliance_components) if compliance_components else ComplianceStatus.COMPLIANT
        )
    
    # Analysis methods (enhanced with real calculations)
    def _perform_comprehensive_analysis(self, bom_doc: AIBOMDocument) -> AIBOMAnalysis:
        """Perform comprehensive analysis"""
        analysis_id = str(uuid.uuid4())
        
        # Calculate scores based on actual components
        risk_score = self._calculate_risk_score(bom_doc.components)
        compliance_score = self._calculate_compliance_score(bom_doc.components)
        security_score = self._calculate_security_score(bom_doc.components)
        performance_score = self._calculate_performance_score(bom_doc.components)
        
        return AIBOMAnalysis(
            id=analysis_id,
            bom_id=bom_doc.id,
            analysis_type="comprehensive",
            risk_score=risk_score,
            compliance_score=compliance_score,
            security_score=security_score,
            performance_score=performance_score,
            cost_analysis=self._calculate_cost_analysis(bom_doc.components),
            recommendations=self._generate_analysis_recommendations(bom_doc),
            created_at=datetime.now()
        )
    
    def _perform_risk_analysis(self, bom_doc: AIBOMDocument) -> AIBOMAnalysis:
        """Perform risk-focused analysis"""
        analysis_id = str(uuid.uuid4())
        
        risk_score = self._calculate_risk_score(bom_doc.components)
        
        return AIBOMAnalysis(
            id=analysis_id,
            bom_id=bom_doc.id,
            analysis_type="risk",
            risk_score=risk_score,
            compliance_score=0.0,
            security_score=0.0,
            performance_score=0.0,
            cost_analysis={},
            recommendations=self._generate_risk_recommendations(bom_doc),
            created_at=datetime.now()
        )
    
    def _perform_compliance_analysis(self, bom_doc: AIBOMDocument) -> AIBOMAnalysis:
        """Perform compliance-focused analysis"""
        analysis_id = str(uuid.uuid4())
        
        compliance_score = self._calculate_compliance_score(bom_doc.components)
        
        return AIBOMAnalysis(
            id=analysis_id,
            bom_id=bom_doc.id,
            analysis_type="compliance",
            risk_score=0.0,
            compliance_score=compliance_score,
            security_score=0.0,
            performance_score=0.0,
            cost_analysis={},
            recommendations=self._generate_compliance_recommendations(bom_doc),
            created_at=datetime.now()
        )
    
    def _perform_security_analysis(self, bom_doc: AIBOMDocument) -> AIBOMAnalysis:
        """Perform security-focused analysis"""
        analysis_id = str(uuid.uuid4())
        
        security_score = self._calculate_security_score(bom_doc.components)
        
        return AIBOMAnalysis(
            id=analysis_id,
            bom_id=bom_doc.id,
            analysis_type="security",
            risk_score=0.0,
            compliance_score=0.0,
            security_score=security_score,
            performance_score=0.0,
            cost_analysis={},
            recommendations=self._generate_security_recommendations(bom_doc),
            created_at=datetime.now()
        )
    
    def _perform_performance_analysis(self, bom_doc: AIBOMDocument) -> AIBOMAnalysis:
        """Perform performance-focused analysis"""
        analysis_id = str(uuid.uuid4())
        
        performance_score = self._calculate_performance_score(bom_doc.components)
        
        return AIBOMAnalysis(
            id=analysis_id,
            bom_id=bom_doc.id,
            analysis_type="performance",
            risk_score=0.0,
            compliance_score=0.0,
            security_score=0.0,
            performance_score=performance_score,
            cost_analysis={},
            recommendations=self._generate_performance_recommendations(bom_doc),
            created_at=datetime.now()
        )
    
    def _perform_cost_analysis(self, bom_doc: AIBOMDocument) -> AIBOMAnalysis:
        """Perform cost-focused analysis"""
        analysis_id = str(uuid.uuid4())
        
        cost_analysis = self._calculate_cost_analysis(bom_doc.components)
        
        return AIBOMAnalysis(
            id=analysis_id,
            bom_id=bom_doc.id,
            analysis_type="cost",
            risk_score=0.0,
            compliance_score=0.0,
            security_score=0.0,
            performance_score=0.0,
            cost_analysis=cost_analysis,
            recommendations=self._generate_cost_recommendations(bom_doc),
            created_at=datetime.now()
        )
    
    def _perform_vulnerability_analysis(self, bom_doc: AIBOMDocument) -> AIBOMAnalysis:
        """Perform vulnerability-focused analysis"""
        analysis_id = str(uuid.uuid4())
        
        # Calculate vulnerability score based on security components
        security_components = [comp for comp in bom_doc.components if comp.type == ComponentType.SECURITY]
        vulnerability_score = self._calculate_vulnerability_score(bom_doc.components)
        
        return AIBOMAnalysis(
            id=analysis_id,
            bom_id=bom_doc.id,
            analysis_type="vulnerability",
            risk_score=vulnerability_score,
            compliance_score=0.0,
            security_score=vulnerability_score,
            performance_score=0.0,
            cost_analysis={},
            recommendations=self._generate_vulnerability_recommendations(bom_doc),
            created_at=datetime.now()
        )
    
    def _perform_sustainability_analysis(self, bom_doc: AIBOMDocument) -> AIBOMAnalysis:
        """Perform sustainability-focused analysis"""
        analysis_id = str(uuid.uuid4())
        
        sustainability_score = self._calculate_sustainability_score(bom_doc.components)
        
        return AIBOMAnalysis(
            id=analysis_id,
            bom_id=bom_doc.id,
            analysis_type="sustainability",
            risk_score=0.0,
            compliance_score=0.0,
            security_score=0.0,
            performance_score=sustainability_score,
            cost_analysis=self._calculate_sustainability_cost_analysis(bom_doc.components),
            recommendations=self._generate_sustainability_recommendations(bom_doc),
            created_at=datetime.now()
        )
    
    # Score calculation methods
    def _calculate_risk_score(self, components: List[AIBOMComponent]) -> float:
        """Calculate normalized risk score"""
        if not components:
            return 0.0
        
        risk_weights = {
            RiskLevel.LOW: 0.25,
            RiskLevel.MEDIUM: 0.5,
            RiskLevel.HIGH: 0.75,
            RiskLevel.CRITICAL: 1.0
        }
        
        total_score = sum(risk_weights[comp.risk_level] for comp in components)
        return total_score / len(components)
    
    def _calculate_compliance_score(self, components: List[AIBOMComponent]) -> float:
        """Calculate normalized compliance score"""
        if not components:
            return 1.0
        
        compliance_weights = {
            ComplianceStatus.COMPLIANT: 1.0,
            ComplianceStatus.PENDING: 0.5,
            ComplianceStatus.REVIEW_REQUIRED: 0.25,
            ComplianceStatus.NON_COMPLIANT: 0.0
        }
        
        total_score = sum(compliance_weights[comp.compliance_status] for comp in components)
        return total_score / len(components)
    
    def _calculate_security_score(self, components: List[AIBOMComponent]) -> float:
        """Calculate security score based on security components"""
        security_components = [comp for comp in components if comp.type == ComponentType.SECURITY]
        if not security_components:
            return 0.5  # Default score if no security components
        
        return self._calculate_compliance_score(security_components)
    
    def _calculate_performance_score(self, components: List[AIBOMComponent]) -> float:
        """Calculate performance score based on monitoring components"""
        monitoring_components = [comp for comp in components if comp.type == ComponentType.MONITORING]
        if not monitoring_components:
            return 0.5  # Default score if no monitoring components
        
        return self._calculate_compliance_score(monitoring_components)
    
    def _calculate_cost_analysis(self, components: List[AIBOMComponent]) -> Dict[str, Any]:
        """Calculate cost analysis"""
        return {
            "total_components": len(components),
            "estimated_cost": len(components) * 100,  # Placeholder calculation
            "cost_breakdown": {
                "infrastructure": len([c for c in components if c.type == ComponentType.INFRASTRUCTURE]) * 50,
                "development": len([c for c in components if c.type == ComponentType.MODEL]) * 75,
                "monitoring": len([c for c in components if c.type == ComponentType.MONITORING]) * 25
            }
        }
    
    def _calculate_vulnerability_score(self, components: List[AIBOMComponent]) -> float:
        """Calculate vulnerability score based on security components"""
        security_components = [comp for comp in components if comp.type == ComponentType.SECURITY]
        if not security_components:
            return 0.8  # High vulnerability if no security components
        
        # Lower score means fewer vulnerabilities
        return 1.0 - self._calculate_compliance_score(security_components)
    
    def _calculate_sustainability_score(self, components: List[AIBOMComponent]) -> float:
        """Calculate sustainability score"""
        if not components:
            return 0.5
        
        # Simple sustainability scoring based on component types
        sustainability_weights = {
            ComponentType.INFRASTRUCTURE: 0.3,  # Infrastructure has environmental impact
            ComponentType.MODEL: 0.2,  # Models can be energy intensive
            ComponentType.MONITORING: 0.1,  # Monitoring has minimal impact
            ComponentType.SECURITY: 0.1,  # Security has minimal impact
            ComponentType.COMPLIANCE: 0.1,  # Compliance has minimal impact
            ComponentType.DATA: 0.1,  # Data has minimal impact
            ComponentType.FRAMEWORK: 0.05,  # Frameworks have minimal impact
            ComponentType.DEPLOYMENT: 0.05  # Deployment has minimal impact
        }
        
        total_score = sum(sustainability_weights.get(comp.type, 0.1) for comp in components)
        return min(1.0, total_score / len(components))
    
    def _calculate_sustainability_cost_analysis(self, components: List[AIBOMComponent]) -> Dict[str, Any]:
        """Calculate sustainability cost analysis"""
        sustainability_score = self._calculate_sustainability_score(components)
        
        return {
            "sustainability_score": sustainability_score,
            "environmental_impact": "medium" if sustainability_score > 0.5 else "low",
            "energy_efficiency": "low" if sustainability_score > 0.7 else "medium",
            "recommendations": [
                "Consider using energy-efficient infrastructure",
                "Optimize model training for reduced energy consumption",
                "Implement green computing practices"
            ]
        }
    
    # Recommendation generation methods
    def _generate_analysis_recommendations(self, bom_doc: AIBOMDocument) -> List[str]:
        """Generate comprehensive analysis recommendations"""
        recommendations = []
        
        if bom_doc.overall_risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            recommendations.append("Consider implementing additional risk mitigation strategies")
        
        if bom_doc.overall_compliance_status != ComplianceStatus.COMPLIANT:
            recommendations.append("Address compliance issues before deployment")
        
        if len([c for c in bom_doc.components if c.type == ComponentType.SECURITY]) < 2:
            recommendations.append("Add more security components to improve protection")
        
        if len([c for c in bom_doc.components if c.type == ComponentType.MONITORING]) < 1:
            recommendations.append("Implement monitoring components for better observability")
        
        return recommendations
    
    def _generate_risk_recommendations(self, bom_doc: AIBOMDocument) -> List[str]:
        """Generate risk-focused recommendations"""
        recommendations = []
        
        high_risk_components = [c for c in bom_doc.components if c.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]]
        
        if high_risk_components:
            recommendations.append(f"Review {len(high_risk_components)} high-risk components")
            recommendations.append("Consider risk mitigation strategies for critical components")
        
        return recommendations
    
    def _generate_compliance_recommendations(self, bom_doc: AIBOMDocument) -> List[str]:
        """Generate compliance-focused recommendations"""
        recommendations = []
        
        non_compliant = [c for c in bom_doc.components if c.compliance_status == ComplianceStatus.NON_COMPLIANT]
        
        if non_compliant:
            recommendations.append(f"Address {len(non_compliant)} non-compliant components")
        
        return recommendations
    
    def _generate_security_recommendations(self, bom_doc: AIBOMDocument) -> List[str]:
        """Generate security-focused recommendations"""
        return ["Implement security best practices", "Regular security audits recommended"]
    
    def _generate_performance_recommendations(self, bom_doc: AIBOMDocument) -> List[str]:
        """Generate performance-focused recommendations"""
        return ["Monitor performance metrics", "Optimize resource usage"]
    
    def _generate_cost_recommendations(self, bom_doc: AIBOMDocument) -> List[str]:
        """Generate cost-focused recommendations"""
        return ["Review component costs", "Consider cost optimization strategies"]
    
    def _generate_vulnerability_recommendations(self, bom_doc: AIBOMDocument) -> List[str]:
        """Generate vulnerability-focused recommendations"""
        recommendations = []
        
        security_components = [c for c in bom_doc.components if c.type == ComponentType.SECURITY]
        
        if len(security_components) < 2:
            recommendations.append("Add more security components to reduce vulnerabilities")
        
        high_risk_components = [c for c in bom_doc.components if c.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]]
        if high_risk_components:
            recommendations.append(f"Address {len(high_risk_components)} high-risk components to reduce vulnerabilities")
        
        recommendations.extend([
            "Implement regular vulnerability scanning",
            "Keep all components updated to latest secure versions",
            "Consider using security-focused frameworks and tools"
        ])
        
        return recommendations
    
    def _generate_sustainability_recommendations(self, bom_doc: AIBOMDocument) -> List[str]:
        """Generate sustainability-focused recommendations"""
        recommendations = []
        
        infra_components = [c for c in bom_doc.components if c.type == ComponentType.INFRASTRUCTURE]
        model_components = [c for c in bom_doc.components if c.type == ComponentType.MODEL]
        
        if len(infra_components) > 3:
            recommendations.append("Consider consolidating infrastructure components to reduce energy consumption")
        
        if len(model_components) > 2:
            recommendations.append("Optimize model training and inference for energy efficiency")
        
        recommendations.extend([
            "Use energy-efficient cloud providers and data centers",
            "Implement auto-scaling to reduce idle resource consumption",
            "Consider using green computing frameworks and tools",
            "Monitor and optimize energy usage patterns"
        ])
        
        return recommendations
    
    # Assessment generation methods
    def _generate_risk_assessment(self, components: List[AIBOMComponent]) -> Dict[str, Any]:
        """Generate detailed risk assessment with normalized scoring"""
        if not components:
            return {
                "overall_risk_level": RiskLevel.LOW.value,
                "risk_distribution": {level.value: 0 for level in RiskLevel},
                "high_risk_components": [],
                "risk_score": 0.0
            }
        
        risk_counts = {level: 0 for level in RiskLevel}
        risk_scores = {
            RiskLevel.LOW: 1,
            RiskLevel.MEDIUM: 2,
            RiskLevel.HIGH: 3,
            RiskLevel.CRITICAL: 4
        }
        
        for comp in components:
            risk_counts[comp.risk_level] += 1
        
        # Calculate normalized risk score
        total_score = sum(risk_scores[comp.risk_level] for comp in components)
        max_possible_score = len(components) * max(risk_scores.values())
        normalized_risk_score = total_score / max_possible_score if max_possible_score > 0 else 0.0
        
        return {
            "overall_risk_level": self._calculate_overall_risk(components).value,
            "risk_distribution": {level.value: count for level, count in risk_counts.items()},
            "high_risk_components": [comp.name for comp in components if comp.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]],
            "risk_score": normalized_risk_score,
            "risk_percentage": {
                level.value: (count / len(components)) * 100 for level, count in risk_counts.items()
            }
        }
    
    def _generate_compliance_report(self, components: List[AIBOMComponent]) -> Dict[str, Any]:
        """Generate detailed compliance report with percentages"""
        if not components:
            return {
                "overall_compliance_status": ComplianceStatus.COMPLIANT.value,
                "compliance_distribution": {status.value: 0 for status in ComplianceStatus},
                "non_compliant_components": [],
                "compliance_score": 1.0
            }
        
        compliance_counts = {status: 0 for status in ComplianceStatus}
        for comp in components:
            compliance_counts[comp.compliance_status] += 1
        
        return {
            "overall_compliance_status": self._calculate_overall_compliance(components).value,
            "compliance_distribution": {status.value: count for status, count in compliance_counts.items()},
            "compliance_percentage": {
                status.value: (count / len(components)) * 100 for status, count in compliance_counts.items()
            },
            "non_compliant_components": [comp.name for comp in components if comp.compliance_status == ComplianceStatus.NON_COMPLIANT],
            "review_required_components": [comp.name for comp in components if comp.compliance_status == ComplianceStatus.REVIEW_REQUIRED],
            "compliance_score": self._calculate_compliance_score(components)
        }
    
    def _generate_recommendations(self, components: List[AIBOMComponent]) -> List[str]:
        """Generate general recommendations"""
        recommendations = []
        
        if len(components) < 3:
            recommendations.append("Consider adding more components for comprehensive coverage")
        
        high_risk_count = len([c for c in components if c.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]])
        if high_risk_count > 0:
            recommendations.append(f"Review {high_risk_count} high-risk components")
        
        return recommendations

# Factory function for creating service instances
async def create_ai_bom_service(config: Optional[DatabaseConfig] = None) -> AIBOMDatabaseService:
    """Factory function to create and initialize AI BOM service"""
    service = AIBOMDatabaseService(config)
    await service.initialize()
    return service

# Example usage and integration methods
async def export_to_external_tool(bom_doc: AIBOMDocument, tool_name: str) -> Dict[str, Any]:
    """Export BOM to external compliance/security tools"""
    if tool_name.lower() == "anchore":
        return {
            "format": "anchore",
            "data": bom_doc.dict(),
            "metadata": {
                "exported_at": datetime.now().isoformat(),
                "tool_version": "1.0.0"
            }
        }
    elif tool_name.lower() == "dependencytrack":
        return {
            "format": "dependencytrack",
            "data": bom_doc.dict(),
            "metadata": {
                "exported_at": datetime.now().isoformat(),
                "tool_version": "1.0.0"
            }
        }
    else:
        raise ValueError(f"Unsupported external tool: {tool_name}")

def calculate_component_metrics(components: List[AIBOMComponent]) -> Dict[str, Any]:
    """Calculate comprehensive component metrics"""
    if not components:
        return {}
    
    metrics = {
        "total_components": len(components),
        "by_type": {},
        "by_risk_level": {},
        "by_compliance_status": {},
        "average_risk_score": 0.0,
        "average_compliance_score": 0.0
    }
    
    # Count by type
    for comp in components:
        comp_type = comp.type.value
        if comp_type not in metrics["by_type"]:
            metrics["by_type"][comp_type] = 0
        metrics["by_type"][comp_type] += 1
    
    # Count by risk level
    for comp in components:
        risk_level = comp.risk_level.value
        if risk_level not in metrics["by_risk_level"]:
            metrics["by_risk_level"][risk_level] = 0
        metrics["by_risk_level"][risk_level] += 1
    
    # Count by compliance status
    for comp in components:
        compliance_status = comp.compliance_status.value
        if compliance_status not in metrics["by_compliance_status"]:
            metrics["by_compliance_status"][compliance_status] = 0
        metrics["by_compliance_status"][compliance_status] += 1
    
    # Calculate averages
    risk_scores = {
        RiskLevel.LOW: 0.25,
        RiskLevel.MEDIUM: 0.5,
        RiskLevel.HIGH: 0.75,
        RiskLevel.CRITICAL: 1.0
    }
    
    compliance_scores = {
        ComplianceStatus.COMPLIANT: 1.0,
        ComplianceStatus.PENDING: 0.5,
        ComplianceStatus.REVIEW_REQUIRED: 0.25,
        ComplianceStatus.NON_COMPLIANT: 0.0
    }
    
    total_risk = sum(risk_scores[comp.risk_level] for comp in components)
    total_compliance = sum(compliance_scores[comp.compliance_status] for comp in components)
    
    metrics["average_risk_score"] = total_risk / len(components)
    metrics["average_compliance_score"] = total_compliance / len(components)
    
    return metrics
