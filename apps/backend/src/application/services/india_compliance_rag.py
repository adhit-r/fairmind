"""
Retrieval-Augmented Generation (RAG) System for Indian Compliance Regulations

This module provides RAG capabilities for querying Indian AI compliance regulations
including DPDP Act 2023, NITI Aayog principles, and MeitY guidelines.

Features:
- Document indexing and embedding
- Semantic similarity search
- Context-aware retrieval
- Multi-framework support
"""

from typing import Dict, List, Any, Optional, Tuple
import logging
import json
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class DocumentType(str, Enum):
    """Types of regulatory documents"""
    DPDP_ACT = "dpdp_act_2023"
    NITI_AAYOG = "niti_aayog_principles"
    MEITY_GUIDELINES = "meity_guidelines"
    DIGITAL_INDIA_ACT = "digital_india_act"


class IndiaComplianceRAG:
    """
    Retrieval-Augmented Generation system for Indian compliance regulations.
    
    Provides semantic search and retrieval of regulatory documents to support
    compliance Q&A and analysis.
    """

    def __init__(self):
        """Initialize RAG system with regulatory documents"""
        self.documents: List[Dict[str, Any]] = []
        self.document_index: Dict[str, List[int]] = {}
        self.initialized = False
        logger.info("Initialized IndiaComplianceRAG")

    async def index_regulatory_documents(self) -> None:
        """
        Index Indian regulatory documents for RAG.

        Loads and indexes DPDP Act, NITI Aayog principles, and MeitY guidelines
        for semantic search and retrieval.

        Requirements: 8.5
        """
        logger.info("Starting regulatory document indexing...")
        
        # Load all regulatory documents
        documents = [
            self._load_dpdp_act_sections(),
            self._load_niti_aayog_sections(),
            self._load_meity_guidelines_sections(),
            self._load_digital_india_act_sections(),
        ]
        
        # Flatten and index documents
        self.documents = []
        for doc_group in documents:
            self.documents.extend(doc_group)
        
        # Build document index by framework
        self._build_document_index()
        
        self.initialized = True
        logger.info(f"Indexed {len(self.documents)} regulatory document sections")

    async def query(
        self,
        question: str,
        framework: Optional[str] = None,
        top_k: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Query regulatory documents using semantic similarity.

        Retrieves the most relevant regulatory documents based on similarity
        to the user's question.

        Args:
            question: User's compliance question
            framework: Optional framework to filter by (e.g., 'dpdp_act_2023')
            top_k: Number of top results to return (default: 3)

        Returns:
            List of relevant document sections with content and metadata

        Requirements: 8.5
        """
        if not self.initialized:
            await self.index_regulatory_documents()
        
        if not self.documents:
            logger.warning("No documents available for query")
            return []
        
        # Filter by framework if specified
        candidate_docs = self.documents
        if framework:
            candidate_docs = [
                doc for doc in self.documents
                if doc.get("framework") == framework
            ]
        
        if not candidate_docs:
            logger.warning(f"No documents found for framework: {framework}")
            return self.documents[:top_k]
        
        # Perform semantic similarity search
        # For now, use keyword matching as a simple implementation
        # In production, use embeddings and vector similarity
        scored_docs = self._score_documents(question, candidate_docs)
        
        # Return top-k results
        top_results = sorted(scored_docs, key=lambda x: x[1], reverse=True)[:top_k]
        
        logger.info(f"Retrieved {len(top_results)} documents for query: {question[:50]}...")
        
        return [doc for doc, score in top_results]

    async def query_by_section(
        self,
        section_id: str,
        framework: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific regulatory section by ID.

        Args:
            section_id: Section identifier (e.g., 'DPDP_6', 'NITI_2')
            framework: Optional framework filter

        Returns:
            Document section or None if not found

        Requirements: 8.5
        """
        for doc in self.documents:
            if doc.get("section_id") == section_id:
                if framework is None or doc.get("framework") == framework:
                    return doc
        
        return None

    async def search_by_keyword(
        self,
        keyword: str,
        framework: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for documents containing specific keywords.

        Args:
            keyword: Keyword to search for
            framework: Optional framework filter

        Returns:
            List of matching documents

        Requirements: 8.5
        """
        results = []
        keyword_lower = keyword.lower()
        
        for doc in self.documents:
            if framework and doc.get("framework") != framework:
                continue
            
            # Check if keyword appears in content or metadata
            content = doc.get("content", "").lower()
            title = doc.get("title", "").lower()
            
            if keyword_lower in content or keyword_lower in title:
                results.append(doc)
        
        return results

    async def get_framework_overview(
        self,
        framework: str,
    ) -> Dict[str, Any]:
        """
        Get overview of a compliance framework.

        Args:
            framework: Framework identifier

        Returns:
            Framework overview with key sections and requirements

        Requirements: 8.5
        """
        framework_docs = [
            doc for doc in self.documents
            if doc.get("framework") == framework
        ]
        
        if not framework_docs:
            return {"error": f"Framework not found: {framework}"}
        
        return {
            "framework": framework,
            "total_sections": len(framework_docs),
            "sections": [
                {
                    "section_id": doc.get("section_id"),
                    "title": doc.get("title"),
                    "category": doc.get("category"),
                }
                for doc in framework_docs
            ],
            "last_updated": datetime.utcnow().isoformat(),
        }

    # ========================================================================
    # Document Loading Methods
    # ========================================================================

    def _load_dpdp_act_sections(self) -> List[Dict[str, Any]]:
        """Load DPDP Act 2023 sections"""
        return [
            {
                "framework": "dpdp_act_2023",
                "section_id": "DPDP_6",
                "title": "Consent and Processing of Personal Data",
                "category": "Data Collection",
                "content": """
Section 6 - Consent and Processing of Personal Data

Key Requirements:
1. Consent must be explicit and informed
2. Consent must specify the purpose of processing
3. Consent must include a withdrawal mechanism
4. Consent records must be maintained with timestamp
5. Consent must be freely given without coercion
6. Consent must be specific for each purpose

Legal Citation: DPDP Act 2023, Section 6

Implications for AI Systems:
- AI systems must obtain explicit consent before processing personal data
- Consent forms must clearly explain data usage
- Users must be able to withdraw consent at any time
- Consent records must be auditable and timestamped
                """,
                "keywords": ["consent", "processing", "personal data", "explicit", "informed"],
                "source": "DPDP Act 2023",
            },
            {
                "framework": "dpdp_act_2023",
                "section_id": "DPDP_8",
                "title": "Right to Access Personal Data",
                "category": "Individual Rights",
                "content": """
Section 8 - Right to Access Personal Data

Key Requirements:
1. Data principals have the right to access their personal data
2. Access must be provided in a clear and understandable format
3. Access must be provided within 30 days of request
4. No fee can be charged for access
5. Access must include information about data processing

Legal Citation: DPDP Act 2023, Section 8

Implications for AI Systems:
- AI systems must maintain mechanisms to provide data access
- Data must be retrievable in machine-readable format
- Response time must not exceed 30 days
- Access logs must be maintained for audit purposes
                """,
                "keywords": ["access", "right", "personal data", "30 days", "format"],
                "source": "DPDP Act 2023",
            },
            {
                "framework": "dpdp_act_2023",
                "section_id": "DPDP_9",
                "title": "Right to Correction and Erasure",
                "category": "Individual Rights",
                "content": """
Section 9 - Right to Correction and Erasure

Key Requirements:
1. Data principals can request correction of inaccurate data
2. Data principals can request erasure of personal data
3. Corrections must be made within 30 days
4. Erasure must be completed within 30 days
5. Erasure must be irreversible

Legal Citation: DPDP Act 2023, Section 9

Implications for AI Systems:
- AI systems must implement data correction mechanisms
- AI systems must implement secure data deletion procedures
- Deletion must be permanent and non-recoverable
- Audit trails must be maintained for compliance verification
                """,
                "keywords": ["correction", "erasure", "right to be forgotten", "30 days", "inaccurate"],
                "source": "DPDP Act 2023",
            },
            {
                "framework": "dpdp_act_2023",
                "section_id": "DPDP_16",
                "title": "Data Localization and Cross-Border Transfer",
                "category": "Data Storage",
                "content": """
Section 16 - Data Localization and Cross-Border Transfer

Key Requirements:
1. Sensitive personal data must be stored in India
2. Cross-border transfer only to approved countries
3. Data transfer agreements must be in place
4. Recipient country must have adequate data protection
5. Transfer must be documented and auditable

Legal Citation: DPDP Act 2023, Section 16

Implications for AI Systems:
- AI systems must verify data storage location
- Cross-border data flows must be monitored
- Data transfer agreements must be maintained
- Compliance with approved country list must be verified
- Regular audits of data location required
                """,
                "keywords": ["localization", "cross-border", "transfer", "storage", "India"],
                "source": "DPDP Act 2023",
            },
            {
                "framework": "dpdp_act_2023",
                "section_id": "DPDP_17",
                "title": "Significant Data Fiduciary Requirements",
                "category": "Organizational",
                "content": """
Section 17 - Significant Data Fiduciary Requirements

Key Requirements:
1. Data Protection Officer must be appointed
2. Data audits must be conducted regularly
3. Data impact assessments must be performed
4. Grievance redressal mechanism must be established
5. Transparency reports must be published

Legal Citation: DPDP Act 2023, Section 17

Implications for AI Systems:
- Large-scale AI systems must appoint a DPO
- Annual data audits are mandatory
- Impact assessments required for high-risk processing
- Grievance mechanism must be accessible
- Transparency reports must be published annually
                """,
                "keywords": ["significant", "data fiduciary", "DPO", "audit", "impact assessment"],
                "source": "DPDP Act 2023",
            },
            {
                "framework": "dpdp_act_2023",
                "section_id": "DPDP_18",
                "title": "Grievance Redressal Mechanism",
                "category": "Accountability",
                "content": """
Section 18 - Grievance Redressal Mechanism

Key Requirements:
1. Grievance mechanism must be easily accessible
2. Grievances must be acknowledged within 7 days
3. Grievances must be resolved within 30 days
4. Escalation procedure must be documented
5. Grievance records must be maintained

Legal Citation: DPDP Act 2023, Section 18

Implications for AI Systems:
- AI systems must provide accessible complaint channels
- Response time must not exceed 7 days for acknowledgment
- Resolution time must not exceed 30 days
- Escalation procedures must be clearly defined
- All grievances must be logged and tracked
                """,
                "keywords": ["grievance", "redressal", "complaint", "7 days", "30 days"],
                "source": "DPDP Act 2023",
            },
        ]

    def _load_niti_aayog_sections(self) -> List[Dict[str, Any]]:
        """Load NITI Aayog AI Principles sections"""
        return [
            {
                "framework": "niti_aayog_principles",
                "section_id": "NITI_1",
                "title": "Safety and Reliability",
                "category": "Technical",
                "content": """
NITI Aayog Principle 1 - Safety and Reliability

Key Requirements:
1. AI systems must undergo safety testing
2. Failure modes must be identified and mitigated
3. System reliability must be validated
4. Robustness testing against adversarial inputs
5. Performance monitoring in production

Legal Citation: NITI Aayog Responsible AI Principles, Principle 1

Implications for AI Systems:
- Comprehensive safety testing required before deployment
- Failure mode analysis must be documented
- Reliability metrics must be established
- Adversarial robustness testing recommended
- Continuous monitoring in production environment
                """,
                "keywords": ["safety", "reliability", "testing", "robustness", "failure"],
                "source": "NITI Aayog",
            },
            {
                "framework": "niti_aayog_principles",
                "section_id": "NITI_2",
                "title": "Equality",
                "category": "Fairness",
                "content": """
NITI Aayog Principle 2 - Equality

Key Requirements:
1. AI systems must not discriminate based on protected characteristics
2. Bias detection across protected characteristics required
3. Fairness metrics must be monitored
4. Disparate impact must be assessed
5. Mitigation strategies for identified bias

Legal Citation: NITI Aayog Responsible AI Principles, Principle 2

Implications for AI Systems:
- Bias testing across Indian demographics (caste, religion, language, region)
- Fairness metrics must be tracked continuously
- Disparate impact analysis required
- Bias mitigation strategies must be implemented
- Regular fairness audits recommended
                """,
                "keywords": ["equality", "bias", "discrimination", "fairness", "disparate impact"],
                "source": "NITI Aayog",
            },
            {
                "framework": "niti_aayog_principles",
                "section_id": "NITI_3",
                "title": "Inclusivity",
                "category": "Accessibility",
                "content": """
NITI Aayog Principle 3 - Inclusivity

Key Requirements:
1. Support for Indian languages (Hindi, English, regional)
2. Accessibility for persons with disabilities
3. Representation in training data
4. Cultural sensitivity in design
5. Inclusive user interface design

Legal Citation: NITI Aayog Responsible AI Principles, Principle 3

Implications for AI Systems:
- Multilingual support for scheduled Indian languages
- Accessibility compliance (WCAG standards)
- Diverse training data representation
- Cultural sensitivity review required
- Inclusive design principles must be followed
                """,
                "keywords": ["inclusivity", "languages", "accessibility", "diversity", "cultural"],
                "source": "NITI Aayog",
            },
            {
                "framework": "niti_aayog_principles",
                "section_id": "NITI_4",
                "title": "Privacy and Security",
                "category": "Security",
                "content": """
NITI Aayog Principle 4 - Privacy and Security

Key Requirements:
1. Data minimization principles
2. Encryption of sensitive data
3. Access controls and authentication
4. Privacy-by-design implementation
5. Regular security assessments

Legal Citation: NITI Aayog Responsible AI Principles, Principle 4

Implications for AI Systems:
- Collect only necessary data
- Implement strong encryption
- Enforce access controls
- Design privacy into systems from the start
- Conduct regular security audits
                """,
                "keywords": ["privacy", "security", "encryption", "access control", "minimization"],
                "source": "NITI Aayog",
            },
            {
                "framework": "niti_aayog_principles",
                "section_id": "NITI_5",
                "title": "Transparency",
                "category": "Transparency",
                "content": """
NITI Aayog Principle 5 - Transparency

Key Requirements:
1. Model documentation and model cards
2. Decision explanation capability
3. Limitation disclosure
4. Training data documentation
5. Algorithm documentation

Legal Citation: NITI Aayog Responsible AI Principles, Principle 5

Implications for AI Systems:
- Create comprehensive model cards
- Provide decision explanations to users
- Disclose system limitations
- Document training data sources
- Maintain algorithm documentation
                """,
                "keywords": ["transparency", "documentation", "model card", "explanation", "disclosure"],
                "source": "NITI Aayog",
            },
            {
                "framework": "niti_aayog_principles",
                "section_id": "NITI_6",
                "title": "Accountability",
                "category": "Governance",
                "content": """
NITI Aayog Principle 6 - Accountability

Key Requirements:
1. Human oversight mechanisms
2. Audit trails for decisions
3. Grievance redressal mechanism
4. Responsibility assignment
5. Regular audits and reviews

Legal Citation: NITI Aayog Responsible AI Principles, Principle 6

Implications for AI Systems:
- Implement human-in-the-loop decision making
- Maintain comprehensive audit logs
- Establish grievance procedures
- Clearly assign accountability
- Conduct regular compliance audits
                """,
                "keywords": ["accountability", "oversight", "audit", "grievance", "responsibility"],
                "source": "NITI Aayog",
            },
        ]

    def _load_meity_guidelines_sections(self) -> List[Dict[str, Any]]:
        """Load MeitY Guidelines sections"""
        return [
            {
                "framework": "meity_guidelines",
                "section_id": "MEITY_1",
                "title": "Responsible AI Development",
                "category": "Development",
                "content": """
MeitY Guideline 1 - Responsible AI Development

Key Requirements:
1. Ethical review of AI systems
2. Risk assessment during development
3. Responsible data collection
4. Bias mitigation in design
5. Testing for harmful outcomes

Legal Citation: MeitY Guidelines for Responsible AI, Section 1

Implications for AI Systems:
- Conduct ethical review before deployment
- Perform risk assessments
- Ensure responsible data practices
- Implement bias mitigation techniques
- Test for potential harms
                """,
                "keywords": ["responsible", "development", "ethical", "risk", "bias"],
                "source": "MeitY",
            },
            {
                "framework": "meity_guidelines",
                "section_id": "MEITY_2",
                "title": "Algorithmic Accountability",
                "category": "Governance",
                "content": """
MeitY Guideline 2 - Algorithmic Accountability

Key Requirements:
1. Clear accountability for algorithmic decisions
2. Explainability of algorithms
3. Auditability of decision-making
4. Human oversight of critical decisions
5. Regular algorithm audits

Legal Citation: MeitY Guidelines for Responsible AI, Section 2

Implications for AI Systems:
- Assign clear accountability for decisions
- Provide algorithm explanations
- Maintain audit trails
- Implement human oversight
- Conduct regular audits
                """,
                "keywords": ["accountability", "algorithm", "explainability", "audit", "oversight"],
                "source": "MeitY",
            },
            {
                "framework": "meity_guidelines",
                "section_id": "MEITY_3",
                "title": "Ethical Deployment",
                "category": "Deployment",
                "content": """
MeitY Guideline 3 - Ethical Deployment

Key Requirements:
1. Ethical considerations in deployment
2. Impact assessment before deployment
3. Monitoring for unintended consequences
4. Stakeholder engagement
5. Continuous improvement processes

Legal Citation: MeitY Guidelines for Responsible AI, Section 3

Implications for AI Systems:
- Assess ethical implications before deployment
- Conduct impact assessments
- Monitor for negative consequences
- Engage with stakeholders
- Implement continuous improvement
                """,
                "keywords": ["ethical", "deployment", "impact", "monitoring", "stakeholder"],
                "source": "MeitY",
            },
        ]

    def _load_digital_india_act_sections(self) -> List[Dict[str, Any]]:
        """Load Digital India Act sections (emerging framework)"""
        return [
            {
                "framework": "digital_india_act",
                "section_id": "DIA_1",
                "title": "Digital India Act - Emerging Framework",
                "category": "Emerging",
                "content": """
Digital India Act - Emerging Framework

Status: Under Development

Key Areas Being Considered:
1. Digital infrastructure and connectivity
2. Digital services and e-commerce
3. Data governance and protection
4. AI and emerging technologies
5. Digital rights and responsibilities

Note: This framework is still evolving. Requirements may change as legislation develops.

Implications for AI Systems:
- Monitor regulatory developments
- Prepare for potential new requirements
- Engage with regulatory consultations
- Maintain flexibility in compliance approach
                """,
                "keywords": ["digital", "india", "emerging", "framework", "development"],
                "source": "Digital India Act (Draft)",
            },
        ]

    def _build_document_index(self) -> None:
        """Build index of documents by framework"""
        self.document_index = {}
        
        for idx, doc in enumerate(self.documents):
            framework = doc.get("framework", "unknown")
            if framework not in self.document_index:
                self.document_index[framework] = []
            self.document_index[framework].append(idx)

    def _score_documents(
        self,
        question: str,
        documents: List[Dict[str, Any]],
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Score documents based on relevance to question.
        
        Uses keyword matching as a simple implementation.
        In production, use embeddings and vector similarity.
        """
        question_words = set(question.lower().split())
        scored = []
        
        for doc in documents:
            score = 0.0
            
            # Score based on keyword matches
            keywords = doc.get("keywords", [])
            for keyword in keywords:
                if keyword.lower() in question.lower():
                    score += 2.0
            
            # Score based on title match
            title = doc.get("title", "").lower()
            for word in question_words:
                if word in title:
                    score += 1.0
            
            # Score based on content match
            content = doc.get("content", "").lower()
            for word in question_words:
                if word in content:
                    score += 0.5
            
            scored.append((doc, score))
        
        return scored
