"""
Database seeding script for India compliance automation feature.

This script seeds sample India compliance data for testing and demonstration purposes.
It creates:
- Sample compliance evidence records
- Sample compliance results
- Sample bias test results
- Sample compliance reports
- Sample integration credentials
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any
import hashlib

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import Base, get_db_url
from database.india_compliance_models import (
    IndiaComplianceEvidence,
    IndiaComplianceResults,
    IndiaBiasTestResults,
    IndiaComplianceReports,
    IntegrationCredentials,
    IndiaFrameworkEnum,
    ComplianceStatusEnum,
    SeverityLevelEnum,
    BiasTypeEnum,
    IntegrationStatusEnum,
)


class IndiaComplianceSeeder:
    """Seeder for India compliance data"""

    def __init__(self, db_url: str):
        """Initialize seeder with database URL"""
        self.engine = create_engine(db_url)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def seed_all(self) -> None:
        """Seed all India compliance data"""
        print("Starting India compliance data seeding...")
        
        try:
            self.seed_evidence()
            self.seed_compliance_results()
            self.seed_bias_test_results()
            self.seed_compliance_reports()
            self.seed_integration_credentials()
            print("✓ India compliance data seeding completed successfully!")
        except Exception as e:
            print(f"✗ Error during seeding: {str(e)}")
            raise

    def seed_evidence(self) -> None:
        """Seed sample compliance evidence records"""
        print("\nSeeding compliance evidence...")
        db = self.SessionLocal()
        
        try:
            # Clear existing evidence
            db.query(IndiaComplianceEvidence).delete()
            db.commit()
            
            system_id = "system_demo_001"
            user_id = "user_demo_001"
            
            evidence_records = [
                {
                    "system_id": system_id,
                    "control_id": "DL_001",
                    "evidence_type": "data_localization",
                    "evidence_data": {
                        "storage_location": "ap-south-1",
                        "provider": "AWS",
                        "verified": True,
                        "sensitive_data_stored_in_india": True,
                    },
                    "source": "AWS API",
                    "metadata": {
                        "check_timestamp": datetime.utcnow().isoformat(),
                        "region": "Mumbai",
                    }
                },
                {
                    "system_id": system_id,
                    "control_id": "CM_001",
                    "evidence_type": "consent_management",
                    "evidence_data": {
                        "consent_records_found": 150,
                        "valid_consent_percentage": 95.0,
                        "withdrawal_mechanism_present": True,
                        "timestamp_present": True,
                        "purpose_specified": True,
                    },
                    "source": "OneTrust Integration",
                    "metadata": {
                        "check_timestamp": datetime.utcnow().isoformat(),
                        "integration_id": "onetrust_001",
                    }
                },
                {
                    "system_id": system_id,
                    "control_id": "LS_001",
                    "evidence_type": "language_support",
                    "evidence_data": {
                        "supported_languages": ["Hindi", "English", "Tamil", "Telugu", "Bengali"],
                        "language_detection_enabled": True,
                        "multilingual_processing": True,
                        "regional_language_support": True,
                    },
                    "source": "System Configuration",
                    "metadata": {
                        "check_timestamp": datetime.utcnow().isoformat(),
                        "total_languages": 5,
                    }
                },
                {
                    "system_id": system_id,
                    "control_id": "CBT_001",
                    "evidence_type": "cross_border_transfer",
                    "evidence_data": {
                        "data_flows_outside_india": False,
                        "approved_countries": [],
                        "data_transfer_agreements": [],
                        "compliance_verified": True,
                    },
                    "source": "Network Monitoring",
                    "metadata": {
                        "check_timestamp": datetime.utcnow().isoformat(),
                        "monitoring_period_days": 30,
                    }
                },
                {
                    "system_id": system_id,
                    "control_id": "GM_001",
                    "evidence_type": "grievance_mechanism",
                    "evidence_data": {
                        "complaint_system_present": True,
                        "response_time_sla_hours": 48,
                        "escalation_procedure_defined": True,
                        "grievance_resolution_workflow": True,
                        "average_resolution_time_hours": 36,
                    },
                    "source": "System Documentation",
                    "metadata": {
                        "check_timestamp": datetime.utcnow().isoformat(),
                        "total_grievances_handled": 42,
                    }
                },
            ]
            
            for evidence_data in evidence_records:
                # Generate evidence hash
                evidence_str = json.dumps(evidence_data["evidence_data"], sort_keys=True)
                evidence_hash = hashlib.sha256(evidence_str.encode()).hexdigest()
                
                evidence = IndiaComplianceEvidence(
                    system_id=evidence_data["system_id"],
                    control_id=evidence_data["control_id"],
                    evidence_type=evidence_data["evidence_type"],
                    evidence_data=evidence_data["evidence_data"],
                    evidence_hash=evidence_hash,
                    collected_at=datetime.utcnow(),
                    source=evidence_data["source"],
                    metadata=evidence_data["metadata"],
                )
                db.add(evidence)
            
            db.commit()
            print(f"✓ Seeded {len(evidence_records)} evidence records")
            
        finally:
            db.close()

    def seed_compliance_results(self) -> None:
        """Seed sample compliance results"""
        print("Seeding compliance results...")
        db = self.SessionLocal()
        
        try:
            # Clear existing results
            db.query(IndiaComplianceResults).delete()
            db.commit()
            
            system_id = "system_demo_001"
            user_id = "user_demo_001"
            
            compliance_results = [
                {
                    "framework": IndiaFrameworkEnum.DPDP_ACT_2023,
                    "overall_score": 87.5,
                    "status": ComplianceStatusEnum.COMPLIANT,
                    "requirements_met": 14,
                    "total_requirements": 16,
                    "evidence_count": 5,
                    "results": {
                        "consent_management": "PASS",
                        "data_localization": "PASS",
                        "cross_border_transfer": "PASS",
                        "data_principal_rights": "PASS",
                        "children_data_protection": "FAIL",
                        "data_breach_notification": "PASS",
                        "data_retention": "PASS",
                        "significant_data_fiduciary": "PASS",
                    },
                    "gaps": [
                        {
                            "control_id": "DPDP_009",
                            "control_name": "Children's Data Protection",
                            "severity": "HIGH",
                            "remediation": "Implement verifiable parental consent mechanism",
                        }
                    ]
                },
                {
                    "framework": IndiaFrameworkEnum.NITI_AAYOG_PRINCIPLES,
                    "overall_score": 82.0,
                    "status": ComplianceStatusEnum.PARTIAL,
                    "requirements_met": 10,
                    "total_requirements": 12,
                    "evidence_count": 4,
                    "results": {
                        "safety_reliability": "PASS",
                        "equality": "PASS",
                        "inclusivity": "PASS",
                        "privacy_security": "PASS",
                        "transparency": "PARTIAL",
                        "accountability": "PASS",
                        "fairness": "PASS",
                    },
                    "gaps": [
                        {
                            "control_id": "NITI_005",
                            "control_name": "Transparency",
                            "severity": "MEDIUM",
                            "remediation": "Enhance model documentation and decision explanation",
                        }
                    ]
                },
                {
                    "framework": IndiaFrameworkEnum.MEITY_GUIDELINES,
                    "overall_score": 90.0,
                    "status": ComplianceStatusEnum.COMPLIANT,
                    "requirements_met": 9,
                    "total_requirements": 10,
                    "evidence_count": 3,
                    "results": {
                        "responsible_ai": "PASS",
                        "algorithmic_accountability": "PASS",
                        "ethical_deployment": "PASS",
                    },
                    "gaps": []
                },
            ]
            
            for result_data in compliance_results:
                result = IndiaComplianceResults(
                    system_id=system_id,
                    user_id=user_id,
                    framework=result_data["framework"],
                    overall_score=result_data["overall_score"],
                    status=result_data["status"],
                    requirements_met=result_data["requirements_met"],
                    total_requirements=result_data["total_requirements"],
                    evidence_count=result_data["evidence_count"],
                    results=result_data["results"],
                    gaps=result_data["gaps"],
                    timestamp=datetime.utcnow(),
                )
                db.add(result)
            
            db.commit()
            print(f"✓ Seeded {len(compliance_results)} compliance results")
            
        finally:
            db.close()

    def seed_bias_test_results(self) -> None:
        """Seed sample bias test results"""
        print("Seeding bias test results...")
        db = self.SessionLocal()
        
        try:
            # Clear existing results
            db.query(IndiaBiasTestResults).delete()
            db.commit()
            
            system_id = "system_demo_001"
            user_id = "user_demo_001"
            model_id = "model_demo_001"
            
            bias_results = [
                {
                    "test_id": f"bias_test_{uuid.uuid4()}",
                    "bias_type": BiasTypeEnum.CASTE_BIAS,
                    "bias_detected": False,
                    "severity": None,
                    "affected_groups": [],
                    "fairness_metrics": {
                        "demographic_parity_sc_st": 0.98,
                        "demographic_parity_obc": 0.96,
                        "demographic_parity_general": 0.97,
                        "equal_opportunity_sc_st": 0.95,
                        "equal_opportunity_obc": 0.94,
                        "equal_opportunity_general": 0.96,
                    },
                    "recommendations": ["Continue monitoring for caste-based bias"]
                },
                {
                    "test_id": f"bias_test_{uuid.uuid4()}",
                    "bias_type": BiasTypeEnum.RELIGIOUS_BIAS,
                    "bias_detected": True,
                    "severity": SeverityLevelEnum.MEDIUM,
                    "affected_groups": ["Muslim", "Christian"],
                    "fairness_metrics": {
                        "demographic_parity_hindu": 0.92,
                        "demographic_parity_muslim": 0.78,
                        "demographic_parity_christian": 0.75,
                        "demographic_parity_sikh": 0.88,
                        "equal_opportunity_hindu": 0.90,
                        "equal_opportunity_muslim": 0.72,
                        "equal_opportunity_christian": 0.70,
                    },
                    "recommendations": [
                        "Rebalance training data for Muslim and Christian populations",
                        "Apply algorithmic debiasing techniques",
                        "Increase representation of minority religions in test sets"
                    ]
                },
                {
                    "test_id": f"bias_test_{uuid.uuid4()}",
                    "bias_type": BiasTypeEnum.LINGUISTIC_BIAS,
                    "bias_detected": False,
                    "severity": None,
                    "affected_groups": [],
                    "fairness_metrics": {
                        "demographic_parity_hindi": 0.97,
                        "demographic_parity_english": 0.98,
                        "demographic_parity_tamil": 0.96,
                        "demographic_parity_telugu": 0.95,
                        "demographic_parity_bengali": 0.94,
                    },
                    "recommendations": ["Linguistic bias is within acceptable thresholds"]
                },
                {
                    "test_id": f"bias_test_{uuid.uuid4()}",
                    "bias_type": BiasTypeEnum.REGIONAL_BIAS,
                    "bias_detected": False,
                    "severity": None,
                    "affected_groups": [],
                    "fairness_metrics": {
                        "demographic_parity_north": 0.96,
                        "demographic_parity_south": 0.97,
                        "demographic_parity_east": 0.95,
                        "demographic_parity_west": 0.98,
                        "demographic_parity_northeast": 0.92,
                    },
                    "recommendations": ["Regional bias is within acceptable thresholds"]
                },
                {
                    "test_id": f"bias_test_{uuid.uuid4()}",
                    "bias_type": BiasTypeEnum.GENDER_BIAS,
                    "bias_detected": True,
                    "severity": SeverityLevelEnum.LOW,
                    "affected_groups": ["Female"],
                    "fairness_metrics": {
                        "demographic_parity_male": 0.94,
                        "demographic_parity_female": 0.88,
                        "demographic_parity_third_gender": 0.85,
                        "equal_opportunity_male": 0.92,
                        "equal_opportunity_female": 0.84,
                        "equal_opportunity_third_gender": 0.80,
                    },
                    "recommendations": [
                        "Increase female representation in training data",
                        "Monitor gender bias in model predictions"
                    ]
                },
            ]
            
            for bias_data in bias_results:
                bias_result = IndiaBiasTestResults(
                    test_id=bias_data["test_id"],
                    system_id=system_id,
                    user_id=user_id,
                    model_id=model_id,
                    bias_type=bias_data["bias_type"],
                    bias_detected=bias_data["bias_detected"],
                    severity=bias_data["severity"],
                    affected_groups=bias_data["affected_groups"],
                    fairness_metrics=bias_data["fairness_metrics"],
                    recommendations=bias_data["recommendations"],
                    timestamp=datetime.utcnow(),
                )
                db.add(bias_result)
            
            db.commit()
            print(f"✓ Seeded {len(bias_results)} bias test results")
            
        finally:
            db.close()

    def seed_compliance_reports(self) -> None:
        """Seed sample compliance reports"""
        print("Seeding compliance reports...")
        db = self.SessionLocal()
        
        try:
            # Clear existing reports
            db.query(IndiaComplianceReports).delete()
            db.commit()
            
            system_id = "system_demo_001"
            user_id = "user_demo_001"
            
            report = IndiaComplianceReports(
                report_id=f"report_{uuid.uuid4()}",
                system_id=system_id,
                user_id=user_id,
                frameworks=[
                    "dpdp_act_2023",
                    "niti_aayog_principles",
                    "meity_guidelines"
                ],
                overall_score=86.5,
                report_data={
                    "executive_summary": "The AI system demonstrates strong compliance with Indian regulatory frameworks with an overall score of 86.5%. Key strengths include robust data localization controls and comprehensive consent management. Minor gaps exist in children's data protection and transparency mechanisms.",
                    "compliance_by_framework": {
                        "dpdp_act_2023": {
                            "score": 87.5,
                            "status": "COMPLIANT",
                            "requirements_met": 14,
                            "total_requirements": 16,
                        },
                        "niti_aayog_principles": {
                            "score": 82.0,
                            "status": "PARTIAL",
                            "requirements_met": 10,
                            "total_requirements": 12,
                        },
                        "meity_guidelines": {
                            "score": 90.0,
                            "status": "COMPLIANT",
                            "requirements_met": 9,
                            "total_requirements": 10,
                        },
                    },
                    "key_findings": [
                        "Data localization controls are properly implemented",
                        "Consent management system is comprehensive and functional",
                        "Language support covers major Indian languages",
                        "No cross-border data transfers detected",
                        "Grievance mechanism is operational",
                    ],
                    "recommendations": [
                        "Implement verifiable parental consent for children's data",
                        "Enhance model documentation and explainability",
                        "Conduct quarterly bias audits for religious demographics",
                    ],
                    "legal_citations": [
                        "DPDP Act 2023, Section 6 - Consent Management",
                        "DPDP Act 2023, Section 16 - Data Localization",
                        "NITI Aayog Principles - Inclusivity and Fairness",
                    ],
                },
                generated_at=datetime.utcnow(),
            )
            db.add(report)
            db.commit()
            print("✓ Seeded 1 compliance report")
            
        finally:
            db.close()

    def seed_integration_credentials(self) -> None:
        """Seed sample integration credentials"""
        print("Seeding integration credentials...")
        db = self.SessionLocal()
        
        try:
            # Clear existing credentials
            db.query(IntegrationCredentials).delete()
            db.commit()
            
            user_id = "user_demo_001"
            
            integrations = [
                {
                    "integration_name": "onetrust",
                    "credentials": {
                        "api_key": "demo_onetrust_key_***",
                        "org_id": "demo_org_001",
                        "endpoint": "https://api.onetrust.com",
                    },
                    "status": IntegrationStatusEnum.CONNECTED,
                },
                {
                    "integration_name": "securiti",
                    "credentials": {
                        "api_key": "demo_securiti_key_***",
                        "tenant_id": "demo_tenant_001",
                        "endpoint": "https://api.securiti.ai",
                    },
                    "status": IntegrationStatusEnum.CONNECTED,
                },
                {
                    "integration_name": "sprinto",
                    "credentials": {
                        "api_key": "demo_sprinto_key_***",
                        "endpoint": "https://api.sprinto.com",
                    },
                    "status": IntegrationStatusEnum.DISCONNECTED,
                },
                {
                    "integration_name": "mlflow",
                    "credentials": {
                        "tracking_uri": "http://localhost:5000",
                        "experiment_name": "india_compliance",
                    },
                    "status": IntegrationStatusEnum.CONNECTED,
                },
            ]
            
            for integration_data in integrations:
                integration = IntegrationCredentials(
                    user_id=user_id,
                    integration_name=integration_data["integration_name"],
                    credentials=integration_data["credentials"],
                    status=integration_data["status"],
                    last_sync=datetime.utcnow() if integration_data["status"] == IntegrationStatusEnum.CONNECTED else None,
                )
                db.add(integration)
            
            db.commit()
            print(f"✓ Seeded {len(integrations)} integration credentials")
            
        finally:
            db.close()


def main():
    """Main entry point"""
    db_url = get_db_url()
    
    if not db_url:
        print("Error: DATABASE_URL environment variable not set")
        sys.exit(1)
    
    seeder = IndiaComplianceSeeder(db_url)
    seeder.seed_all()


if __name__ == "__main__":
    main()
