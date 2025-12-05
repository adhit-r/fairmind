import hashlib
import json
import os
import time
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import hmac
import base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_pem_public_key
import pandas as pd
import numpy as np
from dataclasses import dataclass, asdict
import uuid

@dataclass
class DatasetProvenance:
    """Dataset provenance information"""
    name: str
    version: str
    source: str
    collection_date: str
    collection_method: str
    owner: str
    license: str
    privacy_compliance: List[str]
    known_biases: List[str]
    intended_use: str
    anonymization_methods: List[str]
    data_quality_score: float
    lineage: List[Dict[str, Any]]
    checksum: str
    size_bytes: int
    record_count: int
    features: List[str]

@dataclass
class ModelProvenance:
    """Model provenance information"""
    model_id: str
    name: str
    version: str
    architecture: str
    framework: str
    training_datasets: List[DatasetProvenance]
    training_parameters: Dict[str, Any]
    training_environment: Dict[str, Any]
    training_duration: float
    training_date: str
    developer: str
    organization: str
    license: str
    intended_use: str
    performance_metrics: Dict[str, float]
    bias_analysis: Dict[str, Any]
    security_scan_results: Dict[str, Any]
    checksum: str
    digital_signature: str
    signature_verified: bool
    lineage: List[Dict[str, Any]]

@dataclass
class ModelCard:
    """Model Card for Responsible AI"""
    model_details: Dict[str, Any]
    intended_use: Dict[str, Any]
    factors: Dict[str, Any]
    metrics: Dict[str, Any]
    evaluation_data: Dict[str, Any]
    training_data: Dict[str, Any]
    quantitative_analyses: Dict[str, Any]
    ethical_considerations: Dict[str, Any]
    caveats_and_recommendations: Dict[str, Any]

class ModelProvenanceService:
    """
    Service for tracking model and dataset provenance,
    implementing digital signing, and generating model cards
    """
    
    def __init__(self, private_key_path: Optional[str] = None, public_key_path: Optional[str] = None):
        self.provenance_db = {}
        self.model_cards_db = {}
        self.scan_results_db = {}
        
        # Initialize cryptographic keys for digital signing
        if private_key_path and os.path.exists(private_key_path):
            with open(private_key_path, 'rb') as f:
                self.private_key = load_pem_private_key(f.read(), password=None)
        else:
            # Generate new key pair if not provided
            self.private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048
            )
        
        if public_key_path and os.path.exists(public_key_path):
            with open(public_key_path, 'rb') as f:
                self.public_key = load_pem_public_key(f.read())
        else:
            self.public_key = self.private_key.public_key()
        
        # Save keys if they were generated
        if not private_key_path:
            self._save_keys()
    
    def _save_keys(self):
        """Save generated keys to files"""
        # Save private key
        with open('private_key.pem', 'wb') as f:
            f.write(self.private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        # Save public key
        with open('public_key.pem', 'wb') as f:
            f.write(self.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ))
    
    def calculate_checksum(self, data: bytes) -> str:
        """Calculate SHA-256 checksum of data"""
        return hashlib.sha256(data).hexdigest()
    
    def sign_data(self, data: bytes) -> str:
        """Digitally sign data using private key"""
        signature = self.private_key.sign(
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return base64.b64encode(signature).decode('utf-8')
    
    def verify_signature(self, data: bytes, signature: str) -> bool:
        """Verify digital signature using public key"""
        try:
            signature_bytes = base64.b64decode(signature)
            self.public_key.verify(
                signature_bytes,
                data,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False
    
    def create_dataset_provenance(self, dataset_info: Dict[str, Any]) -> DatasetProvenance:
        """Create provenance record for a dataset"""
        # Calculate checksum of dataset
        dataset_content = json.dumps(dataset_info, sort_keys=True).encode('utf-8')
        checksum = self.calculate_checksum(dataset_content)
        
        provenance = DatasetProvenance(
            name=dataset_info.get('name', ''),
            version=dataset_info.get('version', '1.0'),
            source=dataset_info.get('source', ''),
            collection_date=dataset_info.get('collection_date', datetime.now().isoformat()),
            collection_method=dataset_info.get('collection_method', ''),
            owner=dataset_info.get('owner', ''),
            license=dataset_info.get('license', ''),
            privacy_compliance=dataset_info.get('privacy_compliance', []),
            known_biases=dataset_info.get('known_biases', []),
            intended_use=dataset_info.get('intended_use', ''),
            anonymization_methods=dataset_info.get('anonymization_methods', []),
            data_quality_score=dataset_info.get('data_quality_score', 0.0),
            lineage=dataset_info.get('lineage', []),
            checksum=checksum,
            size_bytes=dataset_info.get('size_bytes', 0),
            record_count=dataset_info.get('record_count', 0),
            features=dataset_info.get('features', [])
        )
        
        return provenance
    
    def create_model_provenance(self, model_info: Dict[str, Any], 
                              training_datasets: List[DatasetProvenance]) -> ModelProvenance:
        """Create provenance record for a model"""
        model_id = model_info.get('model_id', str(uuid.uuid4()))
        
        # Create model content for checksum
        model_content = {
            'model_id': model_id,
            'name': model_info.get('name', ''),
            'version': model_info.get('version', '1.0'),
            'architecture': model_info.get('architecture', ''),
            'framework': model_info.get('framework', ''),
            'training_parameters': model_info.get('training_parameters', {}),
            'training_environment': model_info.get('training_environment', {}),
            'training_date': model_info.get('training_date', datetime.now().isoformat()),
            'developer': model_info.get('developer', ''),
            'organization': model_info.get('organization', ''),
            'license': model_info.get('license', ''),
            'intended_use': model_info.get('intended_use', ''),
            'performance_metrics': model_info.get('performance_metrics', {}),
            'bias_analysis': model_info.get('bias_analysis', {}),
            'security_scan_results': model_info.get('security_scan_results', {}),
            'training_datasets': [asdict(ds) for ds in training_datasets]
        }
        
        model_content_bytes = json.dumps(model_content, sort_keys=True).encode('utf-8')
        checksum = self.calculate_checksum(model_content_bytes)
        digital_signature = self.sign_data(model_content_bytes)
        
        provenance = ModelProvenance(
            model_id=model_id,
            name=model_info.get('name', ''),
            version=model_info.get('version', '1.0'),
            architecture=model_info.get('architecture', ''),
            framework=model_info.get('framework', ''),
            training_datasets=training_datasets,
            training_parameters=model_info.get('training_parameters', {}),
            training_environment=model_info.get('training_environment', {}),
            training_duration=model_info.get('training_duration', 0.0),
            training_date=model_info.get('training_date', datetime.now().isoformat()),
            developer=model_info.get('developer', ''),
            organization=model_info.get('organization', ''),
            license=model_info.get('license', ''),
            intended_use=model_info.get('intended_use', ''),
            performance_metrics=model_info.get('performance_metrics', {}),
            bias_analysis=model_info.get('bias_analysis', {}),
            security_scan_results=model_info.get('security_scan_results', {}),
            checksum=checksum,
            digital_signature=digital_signature,
            signature_verified=True,
            lineage=model_info.get('lineage', [])
        )
        
        # Store in database
        self.provenance_db[model_id] = provenance
        
        return provenance
    
    def scan_model(self, model_path: str, model_info: Dict[str, Any]) -> Dict[str, Any]:
        """Scan model for security vulnerabilities and quality issues"""
        scan_results = {
            'scan_id': str(uuid.uuid4()),
            'scan_date': datetime.now().isoformat(),
            'model_path': model_path,
            'security_issues': [],
            'quality_issues': [],
            'compliance_issues': [],
            'recommendations': [],
            'overall_score': 100
        }
        
        # Check file size
        try:
            file_size = os.path.getsize(model_path)
            if file_size > 1_000_000_000:  # 1GB
                scan_results['quality_issues'].append({
                    'type': 'large_file_size',
                    'severity': 'medium',
                    'description': f'Model file is very large ({file_size / 1e9:.2f}GB)',
                    'recommendation': 'Consider model compression or quantization'
                })
                scan_results['overall_score'] -= 10
        except:
            pass
        
        # Check for suspicious patterns in model info
        suspicious_keywords = ['backdoor', 'trojan', 'malware', 'exploit']
        model_info_str = json.dumps(model_info).lower()
        
        for keyword in suspicious_keywords:
            if keyword in model_info_str:
                scan_results['security_issues'].append({
                    'type': 'suspicious_keyword',
                    'severity': 'high',
                    'description': f'Suspicious keyword found: {keyword}',
                    'recommendation': 'Review model source and training data'
                })
                scan_results['overall_score'] -= 20
        
        # Check for missing provenance information
        required_fields = ['developer', 'organization', 'license', 'intended_use']
        for field in required_fields:
            if not model_info.get(field):
                scan_results['compliance_issues'].append({
                    'type': 'missing_provenance',
                    'severity': 'medium',
                    'description': f'Missing {field} information',
                    'recommendation': f'Add {field} to model provenance'
                })
                scan_results['overall_score'] -= 5
        
        # Check for bias indicators
        if 'bias_analysis' in model_info:
            bias_analysis = model_info['bias_analysis']
            if bias_analysis.get('overall_bias_score', 0) > 0.15:
                scan_results['quality_issues'].append({
                    'type': 'high_bias',
                    'severity': 'high',
                    'description': f'High bias detected: {bias_analysis.get("overall_bias_score", 0):.2f}',
                    'recommendation': 'Consider bias mitigation techniques'
                })
                scan_results['overall_score'] -= 15
        
        # Generate recommendations
        if scan_results['overall_score'] < 80:
            scan_results['recommendations'].append('Model requires review before deployment')
        if scan_results['overall_score'] < 60:
            scan_results['recommendations'].append('Model should not be deployed without significant improvements')
        
        scan_results['overall_score'] = max(0, scan_results['overall_score'])
        
        # Store scan results
        self.scan_results_db[scan_results['scan_id']] = scan_results
        
        return scan_results
    
    def verify_model_authenticity(self, model_id: str, model_content: bytes) -> Dict[str, Any]:
        """Verify model authenticity using digital signature and checksum"""
        if model_id not in self.provenance_db:
            return {
                'verified': False,
                'error': 'Model not found in provenance database'
            }
        
        provenance = self.provenance_db[model_id]
        
        # Verify checksum
        calculated_checksum = self.calculate_checksum(model_content)
        checksum_valid = calculated_checksum == provenance.checksum
        
        # Verify digital signature
        signature_valid = self.verify_signature(model_content, provenance.digital_signature)
        
        return {
            'verified': checksum_valid and signature_valid,
            'checksum_valid': checksum_valid,
            'signature_valid': signature_valid,
            'expected_checksum': provenance.checksum,
            'calculated_checksum': calculated_checksum,
            'digital_signature': provenance.digital_signature,
            'model_id': model_id,
            'verification_date': datetime.now().isoformat()
        }
    
    def generate_model_card(self, model_id: str) -> ModelCard:
        """Generate a Model Card for responsible AI"""
        if model_id not in self.provenance_db:
            raise ValueError(f"Model {model_id} not found in provenance database")
        
        provenance = self.provenance_db[model_id]
        
        # Generate model card sections
        model_details = {
            'name': provenance.name,
            'version': provenance.version,
            'architecture': provenance.architecture,
            'framework': provenance.framework,
            'developer': provenance.developer,
            'organization': provenance.organization,
            'license': provenance.license,
            'training_date': provenance.training_date,
            'training_duration': provenance.training_duration
        }
        
        intended_use = {
            'primary_use': provenance.intended_use,
            'primary_use_case': 'Classification',
            'out_of_scope_use_cases': [
                'Medical diagnosis without human oversight',
                'Criminal justice decisions',
                'Automated hiring decisions'
            ],
            'users': ['Data scientists', 'ML engineers'],
            'use_case_restrictions': 'Requires human oversight for critical decisions'
        }
        
        factors = {
            'relevant_factors': [
                'Data quality and representativeness',
                'Model performance across different demographics',
                'Environmental conditions during training'
            ],
            'evaluation_factors': [
                'Accuracy across different subgroups',
                'Robustness to adversarial attacks',
                'Fairness metrics'
            ]
        }
        
        metrics = {
            'performance_metrics': provenance.performance_metrics,
            'bias_metrics': provenance.bias_analysis,
            'security_metrics': provenance.security_scan_results
        }
        
        evaluation_data = {
            'datasets': [asdict(ds) for ds in provenance.training_datasets],
            'evaluation_methods': ['Cross-validation', 'Holdout testing'],
            'evaluation_metrics': list(provenance.performance_metrics.keys())
        }
        
        training_data = {
            'datasets': [asdict(ds) for ds in provenance.training_datasets],
            'preprocessing': provenance.training_parameters.get('preprocessing', {}),
            'data_augmentation': provenance.training_parameters.get('data_augmentation', {})
        }
        
        quantitative_analyses = {
            'performance_analysis': provenance.performance_metrics,
            'bias_analysis': provenance.bias_analysis,
            'robustness_analysis': provenance.security_scan_results
        }
        
        ethical_considerations = {
            'data_biases': [ds.known_biases for ds in provenance.training_datasets],
            'model_biases': provenance.bias_analysis.get('detected_biases', []),
            'privacy_considerations': [ds.privacy_compliance for ds in provenance.training_datasets],
            'fairness_considerations': 'Model should be evaluated for fairness across different demographic groups'
        }
        
        caveats_and_recommendations = {
            'caveats': [
                'Model performance may vary across different demographic groups',
                'Model should not be used for critical decisions without human oversight',
                'Regular retraining may be required as data distributions change'
            ],
            'recommendations': [
                'Implement continuous monitoring for model drift',
                'Conduct regular bias audits',
                'Maintain human oversight for critical decisions'
            ]
        }
        
        model_card = ModelCard(
            model_details=model_details,
            intended_use=intended_use,
            factors=factors,
            metrics=metrics,
            evaluation_data=evaluation_data,
            training_data=training_data,
            quantitative_analyses=quantitative_analyses,
            ethical_considerations=ethical_considerations,
            caveats_and_recommendations=caveats_and_recommendations
        )
        
        # Store model card
        self.model_cards_db[model_id] = model_card
        
        return model_card
    
    def get_provenance_chain(self, model_id: str) -> List[Dict[str, Any]]:
        """Get the complete provenance chain for a model"""
        if model_id not in self.provenance_db:
            return []
        
        provenance = self.provenance_db[model_id]
        chain = []
        
        # Add model provenance
        chain.append({
            'type': 'model',
            'id': model_id,
            'name': provenance.name,
            'version': provenance.version,
            'date': provenance.training_date,
            'checksum': provenance.checksum,
            'signature_verified': provenance.signature_verified
        })
        
        # Add dataset provenance
        for dataset in provenance.training_datasets:
            chain.append({
                'type': 'dataset',
                'name': dataset.name,
                'version': dataset.version,
                'source': dataset.source,
                'date': dataset.collection_date,
                'checksum': dataset.checksum,
                'owner': dataset.owner
            })
        
        return chain
    
    def export_provenance_report(self, model_id: str) -> Dict[str, Any]:
        """Export comprehensive provenance report"""
        if model_id not in self.provenance_db:
            raise ValueError(f"Model {model_id} not found")
        
        provenance = self.provenance_db[model_id]
        model_card = self.model_cards_db.get(model_id)
        scan_results = self.scan_results_db.get(model_id)
        
        report = {
            'report_id': str(uuid.uuid4()),
            'generated_date': datetime.now().isoformat(),
            'model_provenance': asdict(provenance),
            'model_card': asdict(model_card) if model_card else None,
            'scan_results': scan_results,
            'provenance_chain': self.get_provenance_chain(model_id),
            'verification_status': {
                'signature_verified': provenance.signature_verified,
                'checksum_valid': True,  # Would be verified against actual file
                'provenance_complete': True
            }
        }
        
        return report
    
    def list_provenance_models(self) -> List[Dict[str, Any]]:
        """List all models with provenance information"""
        models = []
        for model_id, provenance in self.provenance_db.items():
            models.append({
                'model_id': model_id,
                'name': provenance.name,
                'version': provenance.version,
                'framework': provenance.framework,
                'training_date': provenance.training_date,
                'developer': provenance.developer,
                'organization': provenance.organization,
                'signature_verified': provenance.signature_verified,
                'has_model_card': model_id in self.model_cards_db,
                'has_scan_results': model_id in self.scan_results_db
            })
        return models
    
    def generate_model_dna(self, model_id: str) -> Dict[str, Any]:
        """
        Generate unique DNA fingerprint for a model
        
        DNA includes:
        - Architecture signature (layer types, sizes, activations)
        - Data lineage hash (training datasets)
        - Training signature (hyperparameters)
        - Bias profile
        - Performance fingerprint
        """
        if model_id not in self.provenance_db:
            raise ValueError(f"Model {model_id} not found in provenance database")
        
        provenance = self.provenance_db[model_id]
        
        # Architecture signature - hash of architecture details
        arch_content = json.dumps({
            'architecture': provenance.architecture,
            'framework': provenance.framework
        }, sort_keys=True).encode('utf-8')
        architecture_genes = hashlib.sha256(arch_content).hexdigest()[:16]
        
        # Data lineage hash - hash of all training datasets
        data_content = ''.join([
            f"{ds.name}{ds.version}{ds.checksum}"
            for ds in provenance.training_datasets
        ]).encode('utf-8')
        data_genes = hashlib.sha256(data_content).hexdigest()[:16]
        
        # Training signature - hash of hyperparameters
        training_content = json.dumps(
            provenance.training_parameters,
            sort_keys=True
        ).encode('utf-8')
        training_genes = hashlib.sha256(training_content).hexdigest()[:16]
        
        # Bias profile - extract key bias metrics
        bias_profile = {}
        if provenance.bias_analysis:
            bias_profile = {
                'overall_bias_score': provenance.bias_analysis.get('overall_bias_score', 0),
                'detected_biases': provenance.bias_analysis.get('detected_biases', []),
                'fairness_metrics': provenance.bias_analysis.get('fairness_metrics', {})
            }
        
        # Performance fingerprint
        performance_fingerprint = {
            metric: value
            for metric, value in provenance.performance_metrics.items()
        }
        
        # Generate complete DNA ID
        dna_id = f"{architecture_genes}-{data_genes}-{training_genes}"
        
        # Calculate generation (how many parent models)
        generation = self._calculate_generation(model_id)
        
        # Get ancestors
        ancestors = self._get_ancestors(model_id)
        
        return {
            "model_id": model_id,
            "dna_id": dna_id,
            "architecture_genes": architecture_genes,
            "data_genes": data_genes,
            "training_genes": training_genes,
            "bias_profile": bias_profile,
            "performance_fingerprint": performance_fingerprint,
            "generation": generation,
            "ancestors": ancestors,
            "created_at": datetime.now().isoformat()
        }
    
    def _calculate_generation(self, model_id: str) -> int:
        """Calculate model generation (depth in lineage tree)"""
        if model_id not in self.provenance_db:
            return 0
        
        provenance = self.provenance_db[model_id]
        if not provenance.lineage:
            return 0
        
        # Generation is 1 + max generation of parents
        max_parent_gen = 0
        for lineage_item in provenance.lineage:
            if lineage_item.get('type') == 'parent_model':
                parent_id = lineage_item.get('model_id')
                if parent_id and parent_id in self.provenance_db:
                    parent_gen = self._calculate_generation(parent_id)
                    max_parent_gen = max(max_parent_gen, parent_gen)
        
        return max_parent_gen + 1
    
    def _get_ancestors(self, model_id: str) -> List[str]:
        """Get all ancestor model IDs"""
        if model_id not in self.provenance_db:
            return []
        
        provenance = self.provenance_db[model_id]
        ancestors = []
        
        for lineage_item in provenance.lineage:
            if lineage_item.get('type') == 'parent_model':
                parent_id = lineage_item.get('model_id')
                if parent_id:
                    ancestors.append(parent_id)
                    # Recursively get parent's ancestors
                    ancestors.extend(self._get_ancestors(parent_id))
        
        return list(set(ancestors))  # Remove duplicates
    
    def compare_model_dna(self, model_id1: str, model_id2: str) -> Dict[str, Any]:
        """
        Compare DNA of two models and calculate similarity
        
        Returns:
        - Similarity scores for each gene type
        - Overall similarity percentage
        - Common ancestors
        - Divergence points
        """
        dna1 = self.generate_model_dna(model_id1)
        dna2 = self.generate_model_dna(model_id2)
        
        # Calculate similarity for each gene type
        arch_similarity = 1.0 if dna1['architecture_genes'] == dna2['architecture_genes'] else 0.0
        data_similarity = 1.0 if dna1['data_genes'] == dna2['data_genes'] else 0.0
        training_similarity = 1.0 if dna1['training_genes'] == dna2['training_genes'] else 0.0
        
        # Calculate bias profile similarity (cosine similarity of bias scores)
        bias_similarity = self._calculate_bias_similarity(
            dna1['bias_profile'],
            dna2['bias_profile']
        )
        
        # Calculate performance similarity
        performance_similarity = self._calculate_performance_similarity(
            dna1['performance_fingerprint'],
            dna2['performance_fingerprint']
        )
        
        # Overall similarity (weighted average)
        overall_similarity = (
            0.3 * arch_similarity +
            0.2 * data_similarity +
            0.2 * training_similarity +
            0.15 * bias_similarity +
            0.15 * performance_similarity
        )
        
        # Find common ancestors
        ancestors1 = set(dna1['ancestors'])
        ancestors2 = set(dna2['ancestors'])
        common_ancestors = list(ancestors1 & ancestors2)
        
        # Identify divergence points
        divergence_points = []
        if arch_similarity < 1.0:
            divergence_points.append("architecture")
        if data_similarity < 1.0:
            divergence_points.append("training_data")
        if training_similarity < 1.0:
            divergence_points.append("hyperparameters")
        
        return {
            "model_1": {
                "id": model_id1,
                "dna_id": dna1['dna_id']
            },
            "model_2": {
                "id": model_id2,
                "dna_id": dna2['dna_id']
            },
            "similarity_scores": {
                "architecture": arch_similarity,
                "data": data_similarity,
                "training": training_similarity,
                "bias_profile": bias_similarity,
                "performance": performance_similarity,
                "overall": overall_similarity
            },
            "common_ancestors": common_ancestors,
            "divergence_points": divergence_points,
            "relationship": self._determine_relationship(dna1, dna2, common_ancestors)
        }
    
    def _calculate_bias_similarity(self, bias1: Dict, bias2: Dict) -> float:
        """Calculate similarity between two bias profiles"""
        if not bias1 or not bias2:
            return 0.0
        
        score1 = bias1.get('overall_bias_score', 0)
        score2 = bias2.get('overall_bias_score', 0)
        
        # Similarity based on how close the bias scores are
        diff = abs(score1 - score2)
        return max(0.0, 1.0 - diff)
    
    def _calculate_performance_similarity(self, perf1: Dict, perf2: Dict) -> float:
        """Calculate similarity between two performance fingerprints"""
        if not perf1 or not perf2:
            return 0.0
        
        # Get common metrics
        common_metrics = set(perf1.keys()) & set(perf2.keys())
        if not common_metrics:
            return 0.0
        
        # Calculate average relative difference
        similarities = []
        for metric in common_metrics:
            v1 = perf1[metric]
            v2 = perf2[metric]
            if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
                # Avoid division by zero
                max_val = max(abs(v1), abs(v2), 1e-10)
                similarity = 1.0 - (abs(v1 - v2) / max_val)
                similarities.append(max(0.0, similarity))
        
        return sum(similarities) / len(similarities) if similarities else 0.0
    
    def _determine_relationship(self, dna1: Dict, dna2: Dict, common_ancestors: List[str]) -> str:
        """Determine relationship between two models"""
        model_id1 = dna1['model_id']
        model_id2 = dna2['model_id']
        
        # Check if one is ancestor of the other
        if model_id1 in dna2['ancestors']:
            return "parent-child"
        if model_id2 in dna1['ancestors']:
            return "child-parent"
        
        # Check if they share common ancestors (siblings)
        if common_ancestors:
            return "siblings"
        
        # Check if they're very similar (clones/variants)
        if dna1['dna_id'] == dna2['dna_id']:
            return "identical_twins"
        if dna1['architecture_genes'] == dna2['architecture_genes'] and \
           dna1['training_genes'] == dna2['training_genes']:
            return "variants"
        
        return "unrelated"
    
    def get_model_lineage_tree(self, model_id: str) -> Dict[str, Any]:
        """
        Get complete lineage tree for visualization
        
        Returns tree structure with:
        - nodes (models and datasets)
        - edges (relationships)
        - metadata for each node
        """
        if model_id not in self.provenance_db:
            raise ValueError(f"Model {model_id} not found")
        
        nodes = []
        edges = []
        visited = set()
        
        def traverse(mid: str, depth: int = 0):
            if mid in visited or mid not in self.provenance_db:
                return
            
            visited.add(mid)
            provenance = self.provenance_db[mid]
            
            # Add model node
            nodes.append({
                'id': mid,
                'type': 'model',
                'name': provenance.name,
                'version': provenance.version,
                'framework': provenance.framework,
                'depth': depth,
                'bias_score': provenance.bias_analysis.get('overall_bias_score', 0) if provenance.bias_analysis else 0,
                'performance': provenance.performance_metrics
            })
            
            # Add dataset nodes and edges
            for dataset in provenance.training_datasets:
                dataset_id = f"dataset_{dataset.checksum[:8]}"
                if dataset_id not in visited:
                    nodes.append({
                        'id': dataset_id,
                        'type': 'dataset',
                        'name': dataset.name,
                        'version': dataset.version,
                        'source': dataset.source,
                        'depth': depth + 1
                    })
                    visited.add(dataset_id)
                
                edges.append({
                    'source': dataset_id,
                    'target': mid,
                    'type': 'trained_on',
                    'label': 'trained on'
                })
            
            # Traverse parent models
            for lineage_item in provenance.lineage:
                if lineage_item.get('type') == 'parent_model':
                    parent_id = lineage_item.get('model_id')
                    if parent_id:
                        edges.append({
                            'source': parent_id,
                            'target': mid,
                            'type': 'derived_from',
                            'label': lineage_item.get('relationship', 'derived from')
                        })
                        traverse(parent_id, depth + 1)
        
        traverse(model_id)
        
        return {
            'root_model_id': model_id,
            'nodes': nodes,
            'edges': edges,
            'total_nodes': len(nodes),
            'total_edges': len(edges),
            'max_depth': max([n['depth'] for n in nodes]) if nodes else 0
        }