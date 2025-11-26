"""
India-specific regulatory framework definitions for AI compliance.

This module defines comprehensive requirements for:
- Digital Personal Data Protection (DPDP) Act 2023
- NITI Aayog AI Principles
- MeitY Guidelines for Responsible AI
- Digital India Act (emerging framework)
"""

from typing import Dict, List, Any
from enum import Enum


# ============================================================================
# DPDP Act 2023 Framework
# ============================================================================

class DPDPActRequirement(str, Enum):
    """DPDP Act 2023 requirement identifiers"""
    CONSENT_MANAGEMENT = "dpdp_001"
    DATA_LOCALIZATION = "dpdp_002"
    CROSS_BORDER_TRANSFER = "dpdp_003"
    DATA_PRINCIPAL_RIGHTS = "dpdp_004"
    CHILDREN_DATA_PROTECTION = "dpdp_005"
    DATA_BREACH_NOTIFICATION = "dpdp_006"
    DATA_RETENTION = "dpdp_007"
    SIGNIFICANT_DATA_FIDUCIARY = "dpdp_008"
    GRIEVANCE_REDRESSAL = "dpdp_009"
    DATA_PROTECTION_OFFICER = "dpdp_010"
    DATA_AUDIT = "dpdp_011"
    DATA_IMPACT_ASSESSMENT = "dpdp_012"
    SECURITY_SAFEGUARDS = "dpdp_013"
    TRANSPARENCY_DISCLOSURE = "dpdp_014"


DPDP_ACT_2023_FRAMEWORK = {
    "framework_id": "dpdp_act_2023",
    "name": "Digital Personal Data Protection (DPDP) Act 2023",
    "description": "India's comprehensive data protection law governing collection, processing, and storage of personal data",
    "version": "1.0",
    "effective_date": "2023-11-12",
    "status": "active",
    "total_requirements": 14,
    "requirements": {
        DPDPActRequirement.CONSENT_MANAGEMENT.value: {
            "requirement_id": DPDPActRequirement.CONSENT_MANAGEMENT.value,
            "name": "Consent Management",
            "description": "Valid consent must be obtained before collecting or processing personal data",
            "legal_citation": "DPDP Act 2023, Section 6",
            "category": "Data Collection",
            "controls": ["CM_001", "CM_002", "CM_003"],
            "key_requirements": [
                "Consent must be explicit and informed",
                "Consent must specify purpose of processing",
                "Consent must include withdrawal mechanism",
                "Consent records must be maintained with timestamp",
                "Consent must be freely given without coercion",
                "Consent must be specific for each purpose"
            ],
            "evidence_types": [
                "consent_records",
                "consent_forms",
                "withdrawal_mechanism",
                "consent_audit_logs"
            ]
        },
        DPDPActRequirement.DATA_LOCALIZATION.value: {
            "requirement_id": DPDPActRequirement.DATA_LOCALIZATION.value,
            "name": "Data Localization",
            "description": "Sensitive personal data must be stored in India",
            "legal_citation": "DPDP Act 2023, Section 16",
            "category": "Data Storage",
            "controls": ["DL_001", "DL_002"],
            "key_requirements": [
                "Sensitive personal data must be stored in India",
                "Data location must be verifiable",
                "Storage location must be documented",
                "Regular audits of data location required",
                "Backup data must also be stored in India"
            ],
            "evidence_types": [
                "data_location_verification",
                "storage_location_audit",
                "geographic_evidence",
                "backup_location_verification"
            ]
        },
        DPDPActRequirement.CROSS_BORDER_TRANSFER.value: {
            "requirement_id": DPDPActRequirement.CROSS_BORDER_TRANSFER.value,
            "name": "Cross-Border Data Transfer",
            "description": "Personal data transfer outside India requires compliance with approved country list",
            "legal_citation": "DPDP Act 2023, Section 16",
            "category": "Data Transfer",
            "controls": ["CBT_001", "CBT_002"],
            "key_requirements": [
                "Cross-border transfers only to approved countries",
                "Data transfer agreements must be in place",
                "Recipient country must have adequate data protection",
                "Transfer must be documented and auditable",
                "Consent required for cross-border transfer"
            ],
            "evidence_types": [
                "data_transfer_agreements",
                "approved_country_list",
                "transfer_audit_logs",
                "recipient_country_assessment"
            ]
        },
        DPDPActRequirement.DATA_PRINCIPAL_RIGHTS.value: {
            "requirement_id": DPDPActRequirement.DATA_PRINCIPAL_RIGHTS.value,
            "name": "Data Principal Rights",
            "description": "Individuals have rights to access, correct, and erase their personal data",
            "legal_citation": "DPDP Act 2023, Sections 8-10",
            "category": "Individual Rights",
            "controls": ["DPR_001", "DPR_002", "DPR_003"],
            "key_requirements": [
                "Right to access personal data",
                "Right to correct inaccurate data",
                "Right to erasure (right to be forgotten)",
                "Right to data portability",
                "Mechanisms to exercise rights must be available",
                "Response to rights requests within 30 days"
            ],
            "evidence_types": [
                "access_request_mechanism",
                "correction_mechanism",
                "erasure_mechanism",
                "data_portability_mechanism",
                "rights_request_logs"
            ]
        },
        DPDPActRequirement.CHILDREN_DATA_PROTECTION.value: {
            "requirement_id": DPDPActRequirement.CHILDREN_DATA_PROTECTION.value,
            "name": "Children's Data Protection",
            "description": "Special protections for personal data of children under 18 years",
            "legal_citation": "DPDP Act 2023, Section 9",
            "category": "Vulnerable Groups",
            "controls": ["CDP_001", "CDP_002"],
            "key_requirements": [
                "Verifiable parental consent required for children's data",
                "Age verification mechanism must be in place",
                "Children's data must be processed with extra care",
                "No profiling of children for commercial purposes",
                "Parental access to children's data must be provided"
            ],
            "evidence_types": [
                "age_verification_mechanism",
                "parental_consent_records",
                "children_data_processing_policy",
                "parental_access_logs"
            ]
        },
        DPDPActRequirement.DATA_BREACH_NOTIFICATION.value: {
            "requirement_id": DPDPActRequirement.DATA_BREACH_NOTIFICATION.value,
            "name": "Data Breach Notification",
            "description": "Data breaches must be reported to Data Protection Board and affected individuals",
            "legal_citation": "DPDP Act 2023, Section 6",
            "category": "Security",
            "controls": ["DBN_001", "DBN_002"],
            "key_requirements": [
                "Breach notification to Data Protection Board within 72 hours",
                "Notification to affected individuals without undue delay",
                "Breach notification must include nature and impact",
                "Breach investigation and remediation required",
                "Breach notification procedures must be documented"
            ],
            "evidence_types": [
                "breach_notification_logs",
                "dpa_notification_records",
                "individual_notification_records",
                "breach_investigation_reports"
            ]
        },
        DPDPActRequirement.DATA_RETENTION.value: {
            "requirement_id": DPDPActRequirement.DATA_RETENTION.value,
            "name": "Data Retention Limits",
            "description": "Personal data must not be retained longer than necessary",
            "legal_citation": "DPDP Act 2023, Section 6",
            "category": "Data Management",
            "controls": ["DR_001", "DR_002"],
            "key_requirements": [
                "Data retention policy must be documented",
                "Data must be deleted after purpose is fulfilled",
                "Retention periods must be justified",
                "Automated deletion mechanisms must be in place",
                "Retention audit logs must be maintained"
            ],
            "evidence_types": [
                "data_retention_policy",
                "deletion_logs",
                "retention_justification",
                "automated_deletion_mechanism"
            ]
        },
        DPDPActRequirement.SIGNIFICANT_DATA_FIDUCIARY.value: {
            "requirement_id": DPDPActRequirement.SIGNIFICANT_DATA_FIDUCIARY.value,
            "name": "Significant Data Fiduciary Requirements",
            "description": "Large-scale data processors must meet additional compliance requirements",
            "legal_citation": "DPDP Act 2023, Section 17",
            "category": "Organizational",
            "controls": ["SDF_001", "SDF_002", "SDF_003"],
            "key_requirements": [
                "Data Protection Officer must be appointed",
                "Data audits must be conducted regularly",
                "Data impact assessments must be performed",
                "Grievance redressal mechanism must be established",
                "Transparency reports must be published"
            ],
            "evidence_types": [
                "dpo_appointment_letter",
                "data_audit_reports",
                "impact_assessment_reports",
                "grievance_mechanism_documentation"
            ]
        },
        DPDPActRequirement.GRIEVANCE_REDRESSAL.value: {
            "requirement_id": DPDPActRequirement.GRIEVANCE_REDRESSAL.value,
            "name": "Grievance Redressal Mechanism",
            "description": "Mechanism to address complaints and grievances from data principals",
            "legal_citation": "DPDP Act 2023, Section 18",
            "category": "Accountability",
            "controls": ["GR_001", "GR_002"],
            "key_requirements": [
                "Grievance mechanism must be easily accessible",
                "Grievances must be acknowledged within 7 days",
                "Grievances must be resolved within 30 days",
                "Escalation procedure must be documented",
                "Grievance records must be maintained"
            ],
            "evidence_types": [
                "grievance_mechanism_documentation",
                "grievance_logs",
                "resolution_records",
                "escalation_procedures"
            ]
        },
        DPDPActRequirement.DATA_PROTECTION_OFFICER.value: {
            "requirement_id": DPDPActRequirement.DATA_PROTECTION_OFFICER.value,
            "name": "Data Protection Officer",
            "description": "Significant data fiduciaries must appoint a Data Protection Officer",
            "legal_citation": "DPDP Act 2023, Section 17",
            "category": "Organizational",
            "controls": ["DPO_001"],
            "key_requirements": [
                "DPO must be appointed for significant data fiduciaries",
                "DPO must be independent and qualified",
                "DPO must have adequate resources",
                "DPO must report to senior management",
                "DPO contact information must be published"
            ],
            "evidence_types": [
                "dpo_appointment_letter",
                "dpo_qualifications",
                "dpo_contact_information",
                "dpo_reporting_structure"
            ]
        },
        DPDPActRequirement.DATA_AUDIT.value: {
            "requirement_id": DPDPActRequirement.DATA_AUDIT.value,
            "name": "Data Audit",
            "description": "Regular audits of data processing activities must be conducted",
            "legal_citation": "DPDP Act 2023, Section 17",
            "category": "Compliance",
            "controls": ["DA_001", "DA_002"],
            "key_requirements": [
                "Data audits must be conducted annually",
                "Audits must cover all data processing activities",
                "Audit reports must be documented",
                "Audit findings must be addressed",
                "Independent auditors should be used"
            ],
            "evidence_types": [
                "audit_reports",
                "audit_scope_documentation",
                "audit_findings",
                "remediation_actions"
            ]
        },
        DPDPActRequirement.DATA_IMPACT_ASSESSMENT.value: {
            "requirement_id": DPDPActRequirement.DATA_IMPACT_ASSESSMENT.value,
            "name": "Data Impact Assessment",
            "description": "Impact assessments must be conducted for high-risk data processing",
            "legal_citation": "DPDP Act 2023, Section 17",
            "category": "Risk Management",
            "controls": ["DIA_001", "DIA_002"],
            "key_requirements": [
                "Impact assessments for high-risk processing",
                "Assessment must identify risks and mitigation",
                "Assessment must be documented",
                "Assessment must be reviewed periodically",
                "Stakeholder consultation may be required"
            ],
            "evidence_types": [
                "impact_assessment_reports",
                "risk_identification",
                "mitigation_strategies",
                "assessment_review_logs"
            ]
        },
        DPDPActRequirement.SECURITY_SAFEGUARDS.value: {
            "requirement_id": DPDPActRequirement.SECURITY_SAFEGUARDS.value,
            "name": "Security Safeguards",
            "description": "Appropriate security measures must be implemented to protect personal data",
            "legal_citation": "DPDP Act 2023, Section 6",
            "category": "Security",
            "controls": ["SS_001", "SS_002", "SS_003"],
            "key_requirements": [
                "Encryption of sensitive personal data",
                "Access controls and authentication",
                "Regular security assessments",
                "Incident response procedures",
                "Employee training on data security"
            ],
            "evidence_types": [
                "encryption_implementation",
                "access_control_logs",
                "security_assessment_reports",
                "incident_response_procedures"
            ]
        },
        DPDPActRequirement.TRANSPARENCY_DISCLOSURE.value: {
            "requirement_id": DPDPActRequirement.TRANSPARENCY_DISCLOSURE.value,
            "name": "Transparency and Disclosure",
            "description": "Organizations must be transparent about data processing activities",
            "legal_citation": "DPDP Act 2023, Section 6",
            "category": "Transparency",
            "controls": ["TD_001", "TD_002"],
            "key_requirements": [
                "Privacy policy must be clear and accessible",
                "Data processing purposes must be disclosed",
                "Data categories must be disclosed",
                "Recipient categories must be disclosed",
                "Retention periods must be disclosed"
            ],
            "evidence_types": [
                "privacy_policy",
                "data_processing_documentation",
                "disclosure_statements",
                "transparency_reports"
            ]
        }
    }
}


# ============================================================================
# NITI Aayog AI Principles Framework
# ============================================================================

class NITIAayogPrinciple(str, Enum):
    """NITI Aayog AI principle identifiers"""
    SAFETY_RELIABILITY = "niti_001"
    EQUALITY = "niti_002"
    INCLUSIVITY = "niti_003"
    PRIVACY_SECURITY = "niti_004"
    TRANSPARENCY = "niti_005"
    ACCOUNTABILITY = "niti_006"
    FAIRNESS = "niti_007"
    HUMAN_AGENCY = "niti_008"
    ROBUSTNESS = "niti_009"
    EXPLAINABILITY = "niti_010"
    CONTINUOUS_LEARNING = "niti_011"
    STAKEHOLDER_ENGAGEMENT = "niti_012"


NITI_AAYOG_PRINCIPLES_FRAMEWORK = {
    "framework_id": "niti_aayog_principles",
    "name": "NITI Aayog Responsible AI Principles",
    "description": "India's national AI strategy principles for responsible and ethical AI development",
    "version": "1.0",
    "effective_date": "2021-06-01",
    "status": "active",
    "total_requirements": 12,
    "requirements": {
        NITIAayogPrinciple.SAFETY_RELIABILITY.value: {
            "requirement_id": NITIAayogPrinciple.SAFETY_RELIABILITY.value,
            "name": "Safety and Reliability",
            "description": "AI systems must be safe, reliable, and robust in operation",
            "legal_citation": "NITI Aayog Responsible AI Principles, Principle 1",
            "category": "Technical",
            "controls": ["SR_001", "SR_002", "SR_003"],
            "key_requirements": [
                "AI systems must undergo safety testing",
                "Failure modes must be identified and mitigated",
                "System reliability must be validated",
                "Robustness testing against adversarial inputs",
                "Performance monitoring in production"
            ],
            "evidence_types": [
                "safety_test_reports",
                "failure_mode_analysis",
                "reliability_metrics",
                "robustness_test_results"
            ]
        },
        NITIAayogPrinciple.EQUALITY.value: {
            "requirement_id": NITIAayogPrinciple.EQUALITY.value,
            "name": "Equality",
            "description": "AI systems must not discriminate based on protected characteristics",
            "legal_citation": "NITI Aayog Responsible AI Principles, Principle 2",
            "category": "Fairness",
            "controls": ["EQ_001", "EQ_002", "EQ_003"],
            "key_requirements": [
                "Bias detection across protected characteristics",
                "Fairness metrics must be monitored",
                "Disparate impact must be assessed",
                "Mitigation strategies for identified bias",
                "Regular fairness audits"
            ],
            "evidence_types": [
                "bias_detection_reports",
                "fairness_metrics",
                "disparate_impact_analysis",
                "bias_mitigation_strategies"
            ]
        },
        NITIAayogPrinciple.INCLUSIVITY.value: {
            "requirement_id": NITIAayogPrinciple.INCLUSIVITY.value,
            "name": "Inclusivity",
            "description": "AI systems must be inclusive and accessible to diverse populations",
            "legal_citation": "NITI Aayog Responsible AI Principles, Principle 3",
            "category": "Accessibility",
            "controls": ["INC_001", "INC_002", "INC_003"],
            "key_requirements": [
                "Support for Indian languages (Hindi, English, regional)",
                "Accessibility for persons with disabilities",
                "Representation in training data",
                "Cultural sensitivity in design",
                "Inclusive user interface design"
            ],
            "evidence_types": [
                "language_support_documentation",
                "accessibility_compliance_reports",
                "training_data_diversity_analysis",
                "cultural_sensitivity_review"
            ]
        },
        NITIAayogPrinciple.PRIVACY_SECURITY.value: {
            "requirement_id": NITIAayogPrinciple.PRIVACY_SECURITY.value,
            "name": "Privacy and Security",
            "description": "AI systems must protect privacy and implement security safeguards",
            "legal_citation": "NITI Aayog Responsible AI Principles, Principle 4",
            "category": "Security",
            "controls": ["PS_001", "PS_002", "PS_003"],
            "key_requirements": [
                "Data minimization principles",
                "Encryption of sensitive data",
                "Access controls and authentication",
                "Privacy-by-design implementation",
                "Regular security assessments"
            ],
            "evidence_types": [
                "data_minimization_policy",
                "encryption_implementation",
                "access_control_logs",
                "security_assessment_reports"
            ]
        },
        NITIAayogPrinciple.TRANSPARENCY.value: {
            "requirement_id": NITIAayogPrinciple.TRANSPARENCY.value,
            "name": "Transparency",
            "description": "AI systems must be transparent about their capabilities and limitations",
            "legal_citation": "NITI Aayog Responsible AI Principles, Principle 5",
            "category": "Transparency",
            "controls": ["TR_001", "TR_002", "TR_003"],
            "key_requirements": [
                "Model documentation and model cards",
                "Decision explanation capability",
                "Limitation disclosure",
                "Training data documentation",
                "Algorithm documentation"
            ],
            "evidence_types": [
                "model_cards",
                "decision_explanation_logs",
                "limitation_documentation",
                "training_data_documentation"
            ]
        },
        NITIAayogPrinciple.ACCOUNTABILITY.value: {
            "requirement_id": NITIAayogPrinciple.ACCOUNTABILITY.value,
            "name": "Accountability",
            "description": "Clear accountability for AI system decisions and impacts",
            "legal_citation": "NITI Aayog Responsible AI Principles, Principle 6",
            "category": "Governance",
            "controls": ["ACC_001", "ACC_002", "ACC_003"],
            "key_requirements": [
                "Human oversight mechanisms",
                "Audit trails for decisions",
                "Grievance redressal mechanism",
                "Responsibility assignment",
                "Regular audits and reviews"
            ],
            "evidence_types": [
                "human_oversight_procedures",
                "audit_trail_logs",
                "grievance_mechanism_documentation",
                "audit_reports"
            ]
        },
        NITIAayogPrinciple.FAIRNESS.value: {
            "requirement_id": NITIAayogPrinciple.FAIRNESS.value,
            "name": "Fairness",
            "description": "AI systems must be fair and equitable across all demographics",
            "legal_citation": "NITI Aayog Responsible AI Principles, Principle 7",
            "category": "Fairness",
            "controls": ["FR_001", "FR_002", "FR_003"],
            "key_requirements": [
                "Demographic parity assessment",
                "Equal opportunity evaluation",
                "Equalized odds measurement",
                "Intersectional fairness analysis",
                "Fairness-aware model development"
            ],
            "evidence_types": [
                "demographic_parity_reports",
                "equal_opportunity_analysis",
                "equalized_odds_metrics",
                "intersectional_analysis"
            ]
        },
        NITIAayogPrinciple.HUMAN_AGENCY.value: {
            "requirement_id": NITIAayogPrinciple.HUMAN_AGENCY.value,
            "name": "Human Agency and Autonomy",
            "description": "AI systems must preserve human agency and autonomy",
            "legal_citation": "NITI Aayog Responsible AI Principles, Principle 8",
            "category": "Governance",
            "controls": ["HA_001", "HA_002"],
            "key_requirements": [
                "Human-in-the-loop decision making",
                "User control over AI decisions",
                "Opt-out mechanisms",
                "Human override capability",
                "Informed consent for AI use"
            ],
            "evidence_types": [
                "human_in_loop_procedures",
                "user_control_mechanisms",
                "opt_out_procedures",
                "consent_documentation"
            ]
        },
        NITIAayogPrinciple.ROBUSTNESS.value: {
            "requirement_id": NITIAayogPrinciple.ROBUSTNESS.value,
            "name": "Robustness",
            "description": "AI systems must be robust to adversarial attacks and edge cases",
            "legal_citation": "NITI Aayog Responsible AI Principles, Principle 9",
            "category": "Technical",
            "controls": ["RB_001", "RB_002"],
            "key_requirements": [
                "Adversarial robustness testing",
                "Edge case handling",
                "Graceful degradation",
                "Error handling and recovery",
                "Performance under stress"
            ],
            "evidence_types": [
                "adversarial_test_reports",
                "edge_case_analysis",
                "error_handling_procedures",
                "stress_test_results"
            ]
        },
        NITIAayogPrinciple.EXPLAINABILITY.value: {
            "requirement_id": NITIAayogPrinciple.EXPLAINABILITY.value,
            "name": "Explainability",
            "description": "AI system decisions must be explainable to stakeholders",
            "legal_citation": "NITI Aayog Responsible AI Principles, Principle 10",
            "category": "Transparency",
            "controls": ["EX_001", "EX_002"],
            "key_requirements": [
                "Feature importance analysis",
                "Decision explanation generation",
                "Model interpretability",
                "Stakeholder-friendly explanations",
                "Explanation validation"
            ],
            "evidence_types": [
                "feature_importance_reports",
                "explanation_samples",
                "interpretability_analysis",
                "explanation_validation_results"
            ]
        },
        NITIAayogPrinciple.CONTINUOUS_LEARNING.value: {
            "requirement_id": NITIAayogPrinciple.CONTINUOUS_LEARNING.value,
            "name": "Continuous Learning and Improvement",
            "description": "AI systems must continuously learn and improve responsibly",
            "legal_citation": "NITI Aayog Responsible AI Principles, Principle 11",
            "category": "Operations",
            "controls": ["CL_001", "CL_002"],
            "key_requirements": [
                "Model performance monitoring",
                "Drift detection mechanisms",
                "Retraining procedures",
                "Feedback loops",
                "Continuous improvement processes"
            ],
            "evidence_types": [
                "performance_monitoring_logs",
                "drift_detection_reports",
                "retraining_procedures",
                "feedback_loop_documentation"
            ]
        },
        NITIAayogPrinciple.STAKEHOLDER_ENGAGEMENT.value: {
            "requirement_id": NITIAayogPrinciple.STAKEHOLDER_ENGAGEMENT.value,
            "name": "Stakeholder Engagement",
            "description": "Engagement with stakeholders in AI development and deployment",
            "legal_citation": "NITI Aayog Responsible AI Principles, Principle 12",
            "category": "Governance",
            "controls": ["SE_001", "SE_002"],
            "key_requirements": [
                "Stakeholder consultation",
                "Community engagement",
                "Feedback mechanisms",
                "Transparency reports",
                "Collaborative governance"
            ],
            "evidence_types": [
                "stakeholder_consultation_records",
                "community_engagement_logs",
                "feedback_mechanism_documentation",
                "transparency_reports"
            ]
        }
    }
}


# ============================================================================
# MeitY Guidelines for Responsible AI Framework
# ============================================================================

class MeitYGuideline(str, Enum):
    """MeitY guideline identifiers"""
    RESPONSIBLE_AI = "meity_001"
    ALGORITHMIC_ACCOUNTABILITY = "meity_002"
    ETHICAL_DEPLOYMENT = "meity_003"
    BIAS_MITIGATION = "meity_004"
    TRANSPARENCY_EXPLAINABILITY = "meity_005"
    HUMAN_OVERSIGHT = "meity_006"
    SECURITY_PRIVACY = "meity_007"
    STAKEHOLDER_ENGAGEMENT = "meity_008"


MEITY_GUIDELINES_FRAMEWORK = {
    "framework_id": "meity_guidelines",
    "name": "MeitY Guidelines for Responsible AI",
    "description": "Ministry of Electronics and Information Technology guidelines for responsible AI deployment in India",
    "version": "1.0",
    "effective_date": "2021-01-01",
    "status": "active",
    "total_requirements": 8,
    "requirements": {
        MeitYGuideline.RESPONSIBLE_AI.value: {
            "requirement_id": MeitYGuideline.RESPONSIBLE_AI.value,
            "name": "Responsible AI Development",
            "description": "AI systems must be developed with responsibility and ethical considerations",
            "legal_citation": "MeitY Guidelines for Responsible AI, Section 1",
            "category": "Development",
            "controls": ["RAI_001", "RAI_002"],
            "key_requirements": [
                "Ethical review of AI systems",
                "Risk assessment during development",
                "Responsible data collection",
                "Bias mitigation in design",
                "Testing for harmful outcomes"
            ],
            "evidence_types": [
                "ethical_review_documentation",
                "risk_assessment_reports",
                "data_collection_procedures",
                "bias_mitigation_strategies"
            ]
        },
        MeitYGuideline.ALGORITHMIC_ACCOUNTABILITY.value: {
            "requirement_id": MeitYGuideline.ALGORITHMIC_ACCOUNTABILITY.value,
            "name": "Algorithmic Accountability",
            "description": "Clear accountability for algorithmic decisions and their impacts",
            "legal_citation": "MeitY Guidelines for Responsible AI, Section 2",
            "category": "Accountability",
            "controls": ["AA_001", "AA_002", "AA_003"],
            "key_requirements": [
                "Algorithm documentation",
                "Decision audit trails",
                "Impact assessment",
                "Responsibility assignment",
                "Remediation procedures"
            ],
            "evidence_types": [
                "algorithm_documentation",
                "audit_trail_logs",
                "impact_assessment_reports",
                "remediation_procedures"
            ]
        },
        MeitYGuideline.ETHICAL_DEPLOYMENT.value: {
            "requirement_id": MeitYGuideline.ETHICAL_DEPLOYMENT.value,
            "name": "Ethical AI Deployment",
            "description": "AI systems must be deployed ethically with consideration for societal impact",
            "legal_citation": "MeitY Guidelines for Responsible AI, Section 3",
            "category": "Deployment",
            "controls": ["ED_001", "ED_002"],
            "key_requirements": [
                "Deployment impact assessment",
                "Stakeholder notification",
                "Monitoring for harmful outcomes",
                "Incident response procedures",
                "Continuous ethical review"
            ],
            "evidence_types": [
                "deployment_impact_assessment",
                "stakeholder_notification_logs",
                "monitoring_procedures",
                "incident_response_plans"
            ]
        },
        MeitYGuideline.BIAS_MITIGATION.value: {
            "requirement_id": MeitYGuideline.BIAS_MITIGATION.value,
            "name": "Bias Mitigation",
            "description": "Systematic approach to identify and mitigate bias in AI systems",
            "legal_citation": "MeitY Guidelines for Responsible AI, Section 4",
            "category": "Fairness",
            "controls": ["BM_001", "BM_002", "BM_003"],
            "key_requirements": [
                "Bias detection mechanisms",
                "Fairness metrics monitoring",
                "Mitigation strategy implementation",
                "Regular bias audits",
                "Stakeholder feedback incorporation"
            ],
            "evidence_types": [
                "bias_detection_reports",
                "fairness_metrics",
                "mitigation_strategies",
                "audit_reports"
            ]
        },
        MeitYGuideline.TRANSPARENCY_EXPLAINABILITY.value: {
            "requirement_id": MeitYGuideline.TRANSPARENCY_EXPLAINABILITY.value,
            "name": "Transparency and Explainability",
            "description": "AI systems must be transparent and decisions must be explainable",
            "legal_citation": "MeitY Guidelines for Responsible AI, Section 5",
            "category": "Transparency",
            "controls": ["TE_001", "TE_002"],
            "key_requirements": [
                "Model transparency documentation",
                "Decision explanation capability",
                "Limitation disclosure",
                "Data source documentation",
                "Public communication of AI use"
            ],
            "evidence_types": [
                "transparency_documentation",
                "explanation_samples",
                "limitation_disclosure",
                "data_documentation"
            ]
        },
        MeitYGuideline.HUMAN_OVERSIGHT.value: {
            "requirement_id": MeitYGuideline.HUMAN_OVERSIGHT.value,
            "name": "Human Oversight",
            "description": "Appropriate human oversight of AI system decisions",
            "legal_citation": "MeitY Guidelines for Responsible AI, Section 6",
            "category": "Governance",
            "controls": ["HO_001", "HO_002"],
            "key_requirements": [
                "Human-in-the-loop mechanisms",
                "Human review procedures",
                "Override capabilities",
                "Training for human reviewers",
                "Decision escalation procedures"
            ],
            "evidence_types": [
                "human_oversight_procedures",
                "review_logs",
                "override_logs",
                "training_documentation"
            ]
        },
        MeitYGuideline.SECURITY_PRIVACY.value: {
            "requirement_id": MeitYGuideline.SECURITY_PRIVACY.value,
            "name": "Security and Privacy",
            "description": "Robust security and privacy protections for AI systems",
            "legal_citation": "MeitY Guidelines for Responsible AI, Section 7",
            "category": "Security",
            "controls": ["SP_001", "SP_002", "SP_003"],
            "key_requirements": [
                "Data encryption",
                "Access controls",
                "Privacy-by-design",
                "Security testing",
                "Incident response"
            ],
            "evidence_types": [
                "encryption_implementation",
                "access_control_logs",
                "privacy_design_documentation",
                "security_test_reports"
            ]
        },
        MeitYGuideline.STAKEHOLDER_ENGAGEMENT.value: {
            "requirement_id": MeitYGuideline.STAKEHOLDER_ENGAGEMENT.value,
            "name": "Stakeholder Engagement",
            "description": "Engagement with stakeholders in AI governance",
            "legal_citation": "MeitY Guidelines for Responsible AI, Section 8",
            "category": "Governance",
            "controls": ["SE_001", "SE_002"],
            "key_requirements": [
                "Stakeholder consultation",
                "Feedback mechanisms",
                "Community engagement",
                "Transparency reports",
                "Collaborative decision-making"
            ],
            "evidence_types": [
                "consultation_records",
                "feedback_logs",
                "engagement_documentation",
                "transparency_reports"
            ]
        }
    }
}


# ============================================================================
# Digital India Act Framework (Emerging)
# ============================================================================

class DigitalIndiaActRequirement(str, Enum):
    """Digital India Act requirement identifiers"""
    DIGITAL_INFRASTRUCTURE = "dia_001"
    DATA_GOVERNANCE = "dia_002"
    DIGITAL_RIGHTS = "dia_003"
    CYBERSECURITY = "dia_004"
    DIGITAL_ACCESSIBILITY = "dia_005"
    DIGITAL_LITERACY = "dia_006"


DIGITAL_INDIA_ACT_FRAMEWORK = {
    "framework_id": "digital_india_act",
    "name": "Digital India Act (Emerging Framework)",
    "description": "Emerging comprehensive digital governance framework for India (draft legislation)",
    "version": "0.1",
    "effective_date": None,
    "status": "emerging",
    "total_requirements": 6,
    "note": "This framework is based on draft legislation and is subject to change. Requirements may be updated as the legislation evolves.",
    "requirements": {
        DigitalIndiaActRequirement.DIGITAL_INFRASTRUCTURE.value: {
            "requirement_id": DigitalIndiaActRequirement.DIGITAL_INFRASTRUCTURE.value,
            "name": "Digital Infrastructure",
            "description": "Robust digital infrastructure for AI and digital services",
            "legal_citation": "Digital India Act (Draft), Section 1",
            "category": "Infrastructure",
            "controls": ["DI_001", "DI_002"],
            "key_requirements": [
                "Reliable digital infrastructure",
                "Interoperability standards",
                "Data center requirements",
                "Network resilience",
                "Infrastructure security"
            ],
            "evidence_types": [
                "infrastructure_documentation",
                "interoperability_compliance",
                "data_center_specifications",
                "resilience_testing"
            ]
        },
        DigitalIndiaActRequirement.DATA_GOVERNANCE.value: {
            "requirement_id": DigitalIndiaActRequirement.DATA_GOVERNANCE.value,
            "name": "Data Governance",
            "description": "Comprehensive data governance framework",
            "legal_citation": "Digital India Act (Draft), Section 2",
            "category": "Governance",
            "controls": ["DG_001", "DG_002"],
            "key_requirements": [
                "Data classification standards",
                "Data ownership clarity",
                "Data sharing frameworks",
                "Data quality standards",
                "Data lifecycle management"
            ],
            "evidence_types": [
                "data_governance_policy",
                "classification_standards",
                "sharing_agreements",
                "quality_metrics"
            ]
        },
        DigitalIndiaActRequirement.DIGITAL_RIGHTS.value: {
            "requirement_id": DigitalIndiaActRequirement.DIGITAL_RIGHTS.value,
            "name": "Digital Rights",
            "description": "Protection of digital rights for all citizens",
            "legal_citation": "Digital India Act (Draft), Section 3",
            "category": "Rights",
            "controls": ["DR_001", "DR_002"],
            "key_requirements": [
                "Right to digital access",
                "Right to digital privacy",
                "Right to digital security",
                "Right to digital identity",
                "Right to digital remedy"
            ],
            "evidence_types": [
                "access_mechanisms",
                "privacy_protections",
                "security_measures",
                "identity_verification",
                "remedy_procedures"
            ]
        },
        DigitalIndiaActRequirement.CYBERSECURITY.value: {
            "requirement_id": DigitalIndiaActRequirement.CYBERSECURITY.value,
            "name": "Cybersecurity",
            "description": "Comprehensive cybersecurity requirements",
            "legal_citation": "Digital India Act (Draft), Section 4",
            "category": "Security",
            "controls": ["CS_001", "CS_002", "CS_003"],
            "key_requirements": [
                "Cybersecurity standards",
                "Threat detection and response",
                "Vulnerability management",
                "Incident reporting",
                "Security awareness training"
            ],
            "evidence_types": [
                "security_standards_documentation",
                "threat_detection_logs",
                "vulnerability_reports",
                "incident_reports",
                "training_records"
            ]
        },
        DigitalIndiaActRequirement.DIGITAL_ACCESSIBILITY.value: {
            "requirement_id": DigitalIndiaActRequirement.DIGITAL_ACCESSIBILITY.value,
            "name": "Digital Accessibility",
            "description": "Ensuring digital services are accessible to all",
            "legal_citation": "Digital India Act (Draft), Section 5",
            "category": "Accessibility",
            "controls": ["DA_001", "DA_002"],
            "key_requirements": [
                "Accessibility standards compliance",
                "Multilingual support",
                "Assistive technology support",
                "Universal design principles",
                "Accessibility testing"
            ],
            "evidence_types": [
                "accessibility_compliance_reports",
                "language_support_documentation",
                "assistive_technology_support",
                "accessibility_test_results"
            ]
        },
        DigitalIndiaActRequirement.DIGITAL_LITERACY.value: {
            "requirement_id": DigitalIndiaActRequirement.DIGITAL_LITERACY.value,
            "name": "Digital Literacy",
            "description": "Promotion of digital literacy and skills",
            "legal_citation": "Digital India Act (Draft), Section 6",
            "category": "Education",
            "controls": ["DL_001", "DL_002"],
            "key_requirements": [
                "Digital literacy programs",
                "Skills development initiatives",
                "Public awareness campaigns",
                "Training resources",
                "Accessibility of learning materials"
            ],
            "evidence_types": [
                "literacy_program_documentation",
                "training_materials",
                "awareness_campaign_records",
                "participation_metrics"
            ]
        }
    }
}


# ============================================================================
# Framework Registry
# ============================================================================

INDIA_COMPLIANCE_FRAMEWORKS = {
    "dpdp_act_2023": DPDP_ACT_2023_FRAMEWORK,
    "niti_aayog_principles": NITI_AAYOG_PRINCIPLES_FRAMEWORK,
    "meity_guidelines": MEITY_GUIDELINES_FRAMEWORK,
    "digital_india_act": DIGITAL_INDIA_ACT_FRAMEWORK,
}


def get_framework(framework_id: str) -> Dict[str, Any]:
    """
    Get a specific framework definition by ID.
    
    Args:
        framework_id: Framework identifier (e.g., 'dpdp_act_2023')
        
    Returns:
        Framework definition dictionary
        
    Raises:
        ValueError: If framework not found
    """
    if framework_id not in INDIA_COMPLIANCE_FRAMEWORKS:
        raise ValueError(f"Framework '{framework_id}' not found. Available frameworks: {list(INDIA_COMPLIANCE_FRAMEWORKS.keys())}")
    return INDIA_COMPLIANCE_FRAMEWORKS[framework_id]


def get_all_frameworks() -> Dict[str, Dict[str, Any]]:
    """
    Get all available framework definitions.
    
    Returns:
        Dictionary of all frameworks
    """
    return INDIA_COMPLIANCE_FRAMEWORKS


def get_framework_requirements(framework_id: str) -> Dict[str, Dict[str, Any]]:
    """
    Get all requirements for a specific framework.
    
    Args:
        framework_id: Framework identifier
        
    Returns:
        Dictionary of requirements
        
    Raises:
        ValueError: If framework not found
    """
    framework = get_framework(framework_id)
    return framework.get("requirements", {})


def get_requirement(framework_id: str, requirement_id: str) -> Dict[str, Any]:
    """
    Get a specific requirement from a framework.
    
    Args:
        framework_id: Framework identifier
        requirement_id: Requirement identifier
        
    Returns:
        Requirement definition dictionary
        
    Raises:
        ValueError: If framework or requirement not found
    """
    requirements = get_framework_requirements(framework_id)
    if requirement_id not in requirements:
        raise ValueError(f"Requirement '{requirement_id}' not found in framework '{framework_id}'")
    return requirements[requirement_id]


def get_framework_summary(framework_id: str) -> Dict[str, Any]:
    """
    Get a summary of a framework without detailed requirements.
    
    Args:
        framework_id: Framework identifier
        
    Returns:
        Framework summary
        
    Raises:
        ValueError: If framework not found
    """
    framework = get_framework(framework_id)
    return {
        "framework_id": framework["framework_id"],
        "name": framework["name"],
        "description": framework["description"],
        "version": framework["version"],
        "effective_date": framework.get("effective_date"),
        "status": framework["status"],
        "total_requirements": framework["total_requirements"],
        "note": framework.get("note")
    }


def list_all_frameworks_summary() -> List[Dict[str, Any]]:
    """
    Get summaries of all available frameworks.
    
    Returns:
        List of framework summaries
    """
    return [get_framework_summary(fid) for fid in INDIA_COMPLIANCE_FRAMEWORKS.keys()]
