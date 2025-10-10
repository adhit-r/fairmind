"""
Evidence Collection and Reporting System
Collects, stores, and reports compliance evidence for AI governance
"""

import json
import yaml
import csv
import io
import base64
from typing import Dict, List, Any, Optional, Union, BinaryIO
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import logging
from pathlib import Path
import uuid
import hashlib
import mimetypes
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import pandas as pd

logger = logging.getLogger(__name__)

class EvidenceType(Enum):
    DOCUMENT = "document"
    DATA = "data"
    CODE = "code"
    LOG = "log"
    METRIC = "metric"
    SCREENSHOT = "screenshot"
    AUDIT_TRAIL = "audit_trail"
    TEST_RESULT = "test_result"
    POLICY_EVALUATION = "policy_evaluation"
    COMPLIANCE_ASSESSMENT = "compliance_assessment"

class EvidenceStatus(Enum):
    PENDING = "pending"
    COLLECTED = "collected"
    VERIFIED = "verified"
    EXPIRED = "expired"
    INVALID = "invalid"

class ReportFormat(Enum):
    PDF = "pdf"
    JSON = "json"
    CSV = "csv"
    EXCEL = "excel"
    HTML = "html"

@dataclass
class EvidenceItem:
    """Represents a piece of compliance evidence"""
    id: str
    name: str
    description: str
    evidence_type: EvidenceType
    status: EvidenceStatus
    system_id: str
    framework: str
    control_id: str
    content: Union[str, bytes, Dict[str, Any]]
    content_type: str
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime]
    verified_by: Optional[str]
    verified_at: Optional[datetime]

@dataclass
class EvidenceCollection:
    """Collection of evidence items for a specific purpose"""
    id: str
    name: str
    description: str
    system_id: str
    framework: str
    purpose: str
    evidence_items: List[str]  # Evidence item IDs
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

@dataclass
class ComplianceReport:
    """Compliance report with evidence"""
    id: str
    title: str
    system_id: str
    framework: str
    report_type: str
    evidence_collections: List[str]  # Collection IDs
    summary: Dict[str, Any]
    findings: List[Dict[str, Any]]
    recommendations: List[str]
    generated_at: datetime
    generated_by: str
    metadata: Dict[str, Any]

class EvidenceCollector:
    """Main evidence collection and reporting service"""
    
    def __init__(self, storage_path: str = "evidence_storage"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.storage_path / "documents").mkdir(exist_ok=True)
        (self.storage_path / "data").mkdir(exist_ok=True)
        (self.storage_path / "logs").mkdir(exist_ok=True)
        (self.storage_path / "reports").mkdir(exist_ok=True)
        
        self.evidence_items: Dict[str, EvidenceItem] = {}
        self.evidence_collections: Dict[str, EvidenceCollection] = {}
        self.compliance_reports: Dict[str, ComplianceReport] = {}
        
        self._load_existing_evidence()
    
    def _load_existing_evidence(self):
        """Load existing evidence from storage"""
        try:
            # Load evidence items
            evidence_file = self.storage_path / "evidence_items.json"
            if evidence_file.exists():
                with open(evidence_file, 'r') as f:
                    evidence_data = json.load(f)
                    for item_data in evidence_data:
                        item = self._dict_to_evidence_item(item_data)
                        self.evidence_items[item.id] = item
            
            # Load evidence collections
            collections_file = self.storage_path / "evidence_collections.json"
            if collections_file.exists():
                with open(collections_file, 'r') as f:
                    collections_data = json.load(f)
                    for collection_data in collections_data:
                        collection = self._dict_to_evidence_collection(collection_data)
                        self.evidence_collections[collection.id] = collection
            
            # Load compliance reports
            reports_file = self.storage_path / "compliance_reports.json"
            if reports_file.exists():
                with open(reports_file, 'r') as f:
                    reports_data = json.load(f)
                    for report_data in reports_data:
                        report = self._dict_to_compliance_report(report_data)
                        self.compliance_reports[report.id] = report
            
            logger.info(f"Loaded {len(self.evidence_items)} evidence items, "
                       f"{len(self.evidence_collections)} collections, "
                       f"{len(self.compliance_reports)} reports")
            
        except Exception as e:
            logger.error(f"Error loading existing evidence: {e}")
    
    def _dict_to_evidence_item(self, data: Dict[str, Any]) -> EvidenceItem:
        """Convert dictionary to EvidenceItem"""
        return EvidenceItem(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            evidence_type=EvidenceType(data["evidence_type"]),
            status=EvidenceStatus(data["status"]),
            system_id=data["system_id"],
            framework=data["framework"],
            control_id=data["control_id"],
            content=data["content"],
            content_type=data["content_type"],
            metadata=data["metadata"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
            verified_by=data.get("verified_by"),
            verified_at=datetime.fromisoformat(data["verified_at"]) if data.get("verified_at") else None
        )
    
    def _dict_to_evidence_collection(self, data: Dict[str, Any]) -> EvidenceCollection:
        """Convert dictionary to EvidenceCollection"""
        return EvidenceCollection(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            system_id=data["system_id"],
            framework=data["framework"],
            purpose=data["purpose"],
            evidence_items=data["evidence_items"],
            metadata=data["metadata"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"])
        )
    
    def _dict_to_compliance_report(self, data: Dict[str, Any]) -> ComplianceReport:
        """Convert dictionary to ComplianceReport"""
        return ComplianceReport(
            id=data["id"],
            title=data["title"],
            system_id=data["system_id"],
            framework=data["framework"],
            report_type=data["report_type"],
            evidence_collections=data["evidence_collections"],
            summary=data["summary"],
            findings=data["findings"],
            recommendations=data["recommendations"],
            generated_at=datetime.fromisoformat(data["generated_at"]),
            generated_by=data["generated_by"],
            metadata=data["metadata"]
        )
    
    def collect_evidence(self, name: str, description: str, evidence_type: EvidenceType,
                        system_id: str, framework: str, control_id: str,
                        content: Union[str, bytes, Dict[str, Any]], 
                        content_type: str = "application/octet-stream",
                        metadata: Dict[str, Any] = None,
                        expires_in_days: int = None) -> EvidenceItem:
        """Collect and store evidence"""
        
        evidence_id = str(uuid.uuid4())
        
        # Calculate expiration date
        expires_at = None
        if expires_in_days:
            expires_at = datetime.now() + timedelta(days=expires_in_days)
        
        # Create evidence item
        evidence_item = EvidenceItem(
            id=evidence_id,
            name=name,
            description=description,
            evidence_type=evidence_type,
            status=EvidenceStatus.COLLECTED,
            system_id=system_id,
            framework=framework,
            control_id=control_id,
            content=content,
            content_type=content_type,
            metadata=metadata or {},
            created_at=datetime.now(),
            updated_at=datetime.now(),
            expires_at=expires_at,
            verified_by=None,
            verified_at=None
        )
        
        # Store evidence
        self.evidence_items[evidence_id] = evidence_item
        
        # Save to file if it's binary content
        if evidence_type in [EvidenceType.DOCUMENT, EvidenceType.SCREENSHOT]:
            self._save_binary_evidence(evidence_item)
        
        # Save metadata
        self._save_evidence_metadata()
        
        logger.info(f"Collected evidence {evidence_id} for system {system_id}")
        return evidence_item
    
    def _save_binary_evidence(self, evidence_item: EvidenceItem):
        """Save binary evidence to file"""
        try:
            # Determine file extension
            ext = mimetypes.guess_extension(evidence_item.content_type) or ".bin"
            
            # Create filename
            filename = f"{evidence_item.id}{ext}"
            
            # Determine storage directory
            if evidence_item.evidence_type == EvidenceType.DOCUMENT:
                storage_dir = self.storage_path / "documents"
            elif evidence_item.evidence_type == EvidenceType.SCREENSHOT:
                storage_dir = self.storage_path / "screenshots"
            else:
                storage_dir = self.storage_path / "data"
            
            # Save file
            file_path = storage_dir / filename
            with open(file_path, 'wb') as f:
                if isinstance(evidence_item.content, bytes):
                    f.write(evidence_item.content)
                else:
                    f.write(str(evidence_item.content).encode())
            
            # Update metadata with file path
            evidence_item.metadata["file_path"] = str(file_path)
            
        except Exception as e:
            logger.error(f"Error saving binary evidence {evidence_item.id}: {e}")
    
    def _save_evidence_metadata(self):
        """Save evidence metadata to JSON files"""
        try:
            # Save evidence items
            evidence_data = []
            for item in self.evidence_items.values():
                item_dict = asdict(item)
                item_dict["created_at"] = item.created_at.isoformat()
                item_dict["updated_at"] = item.updated_at.isoformat()
                item_dict["expires_at"] = item.expires_at.isoformat() if item.expires_at else None
                item_dict["verified_at"] = item.verified_at.isoformat() if item.verified_at else None
                evidence_data.append(item_dict)
            
            with open(self.storage_path / "evidence_items.json", 'w') as f:
                json.dump(evidence_data, f, indent=2)
            
            # Save evidence collections
            collections_data = []
            for collection in self.evidence_collections.values():
                collection_dict = asdict(collection)
                collection_dict["created_at"] = collection.created_at.isoformat()
                collection_dict["updated_at"] = collection.updated_at.isoformat()
                collections_data.append(collection_dict)
            
            with open(self.storage_path / "evidence_collections.json", 'w') as f:
                json.dump(collections_data, f, indent=2)
            
            # Save compliance reports
            reports_data = []
            for report in self.compliance_reports.values():
                report_dict = asdict(report)
                report_dict["generated_at"] = report.generated_at.isoformat()
                reports_data.append(report_dict)
            
            with open(self.storage_path / "compliance_reports.json", 'w') as f:
                json.dump(reports_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving evidence metadata: {e}")
    
    def verify_evidence(self, evidence_id: str, verified_by: str) -> bool:
        """Verify evidence item"""
        if evidence_id not in self.evidence_items:
            return False
        
        evidence_item = self.evidence_items[evidence_id]
        evidence_item.status = EvidenceStatus.VERIFIED
        evidence_item.verified_by = verified_by
        evidence_item.verified_at = datetime.now()
        evidence_item.updated_at = datetime.now()
        
        self._save_evidence_metadata()
        logger.info(f"Verified evidence {evidence_id} by {verified_by}")
        return True
    
    def create_evidence_collection(self, name: str, description: str, system_id: str,
                                 framework: str, purpose: str, 
                                 evidence_item_ids: List[str] = None,
                                 metadata: Dict[str, Any] = None) -> EvidenceCollection:
        """Create an evidence collection"""
        
        collection_id = str(uuid.uuid4())
        
        collection = EvidenceCollection(
            id=collection_id,
            name=name,
            description=description,
            system_id=system_id,
            framework=framework,
            purpose=purpose,
            evidence_items=evidence_item_ids or [],
            metadata=metadata or {},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.evidence_collections[collection_id] = collection
        self._save_evidence_metadata()
        
        logger.info(f"Created evidence collection {collection_id}")
        return collection
    
    def add_evidence_to_collection(self, collection_id: str, evidence_id: str) -> bool:
        """Add evidence item to collection"""
        if collection_id not in self.evidence_collections:
            return False
        
        if evidence_id not in self.evidence_items:
            return False
        
        collection = self.evidence_collections[collection_id]
        if evidence_id not in collection.evidence_items:
            collection.evidence_items.append(evidence_id)
            collection.updated_at = datetime.now()
            self._save_evidence_metadata()
        
        return True
    
    def generate_compliance_report(self, title: str, system_id: str, framework: str,
                                 report_type: str, evidence_collection_ids: List[str],
                                 summary: Dict[str, Any], findings: List[Dict[str, Any]],
                                 recommendations: List[str], generated_by: str,
                                 metadata: Dict[str, Any] = None) -> ComplianceReport:
        """Generate a compliance report"""
        
        report_id = str(uuid.uuid4())
        
        report = ComplianceReport(
            id=report_id,
            title=title,
            system_id=system_id,
            framework=framework,
            report_type=report_type,
            evidence_collections=evidence_collection_ids,
            summary=summary,
            findings=findings,
            recommendations=recommendations,
            generated_at=datetime.now(),
            generated_by=generated_by,
            metadata=metadata or {}
        )
        
        self.compliance_reports[report_id] = report
        self._save_evidence_metadata()
        
        logger.info(f"Generated compliance report {report_id}")
        return report
    
    def export_report(self, report_id: str, format: ReportFormat, 
                     output_path: Optional[str] = None) -> Union[str, bytes]:
        """Export compliance report in specified format"""
        
        if report_id not in self.compliance_reports:
            raise ValueError(f"Report {report_id} not found")
        
        report = self.compliance_reports[report_id]
        
        if format == ReportFormat.PDF:
            return self._export_pdf_report(report, output_path)
        elif format == ReportFormat.JSON:
            return self._export_json_report(report, output_path)
        elif format == ReportFormat.CSV:
            return self._export_csv_report(report, output_path)
        elif format == ReportFormat.EXCEL:
            return self._export_excel_report(report, output_path)
        elif format == ReportFormat.HTML:
            return self._export_html_report(report, output_path)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _export_pdf_report(self, report: ComplianceReport, output_path: Optional[str] = None) -> bytes:
        """Export report as PDF"""
        
        if output_path:
            doc = SimpleDocTemplate(output_path, pagesize=A4)
        else:
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
        
        # Create styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        
        # Build content
        story = []
        
        # Title
        story.append(Paragraph(report.title, title_style))
        story.append(Spacer(1, 12))
        
        # Report metadata
        metadata_data = [
            ['System ID', report.system_id],
            ['Framework', report.framework],
            ['Report Type', report.report_type],
            ['Generated At', report.generated_at.strftime('%Y-%m-%d %H:%M:%S')],
            ['Generated By', report.generated_by]
        ]
        
        metadata_table = Table(metadata_data, colWidths=[2*inch, 4*inch])
        metadata_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(metadata_table)
        story.append(Spacer(1, 20))
        
        # Summary
        story.append(Paragraph("Summary", styles['Heading2']))
        for key, value in report.summary.items():
            story.append(Paragraph(f"<b>{key}:</b> {value}", styles['Normal']))
        story.append(Spacer(1, 12))
        
        # Findings
        if report.findings:
            story.append(Paragraph("Findings", styles['Heading2']))
            for i, finding in enumerate(report.findings, 1):
                story.append(Paragraph(f"{i}. {finding.get('title', 'Finding')}", styles['Heading3']))
                story.append(Paragraph(finding.get('description', ''), styles['Normal']))
                if 'evidence' in finding:
                    story.append(Paragraph(f"Evidence: {finding['evidence']}", styles['Normal']))
                story.append(Spacer(1, 6))
        
        # Recommendations
        if report.recommendations:
            story.append(Paragraph("Recommendations", styles['Heading2']))
            for i, recommendation in enumerate(report.recommendations, 1):
                story.append(Paragraph(f"{i}. {recommendation}", styles['Normal']))
        
        # Build PDF
        doc.build(story)
        
        if output_path:
            return b"PDF saved to file"
        else:
            buffer.seek(0)
            return buffer.getvalue()
    
    def _export_json_report(self, report: ComplianceReport, output_path: Optional[str] = None) -> str:
        """Export report as JSON"""
        
        # Get evidence details
        evidence_details = []
        for collection_id in report.evidence_collections:
            if collection_id in self.evidence_collections:
                collection = self.evidence_collections[collection_id]
                collection_evidence = []
                
                for evidence_id in collection.evidence_items:
                    if evidence_id in self.evidence_items:
                        evidence = self.evidence_items[evidence_id]
                        collection_evidence.append({
                            "id": evidence.id,
                            "name": evidence.name,
                            "type": evidence.evidence_type.value,
                            "status": evidence.status.value,
                            "created_at": evidence.created_at.isoformat()
                        })
                
                evidence_details.append({
                    "collection_id": collection_id,
                    "collection_name": collection.name,
                    "evidence_items": collection_evidence
                })
        
        # Create export data
        export_data = {
            "report": asdict(report),
            "evidence_details": evidence_details,
            "export_timestamp": datetime.now().isoformat()
        }
        
        # Convert datetime objects
        export_data["report"]["generated_at"] = report.generated_at.isoformat()
        
        json_str = json.dumps(export_data, indent=2)
        
        if output_path:
            with open(output_path, 'w') as f:
                f.write(json_str)
            return "JSON saved to file"
        else:
            return json_str
    
    def _export_csv_report(self, report: ComplianceReport, output_path: Optional[str] = None) -> str:
        """Export report as CSV"""
        
        # Create CSV data
        csv_data = []
        
        # Report metadata
        csv_data.append(["Report Metadata", ""])
        csv_data.append(["Title", report.title])
        csv_data.append(["System ID", report.system_id])
        csv_data.append(["Framework", report.framework])
        csv_data.append(["Report Type", report.report_type])
        csv_data.append(["Generated At", report.generated_at.strftime('%Y-%m-%d %H:%M:%S')])
        csv_data.append(["Generated By", report.generated_by])
        csv_data.append(["", ""])
        
        # Summary
        csv_data.append(["Summary", ""])
        for key, value in report.summary.items():
            csv_data.append([key, str(value)])
        csv_data.append(["", ""])
        
        # Findings
        csv_data.append(["Findings", ""])
        csv_data.append(["Title", "Description", "Evidence"])
        for finding in report.findings:
            csv_data.append([
                finding.get('title', ''),
                finding.get('description', ''),
                finding.get('evidence', '')
            ])
        csv_data.append(["", ""])
        
        # Recommendations
        csv_data.append(["Recommendations", ""])
        for i, recommendation in enumerate(report.recommendations, 1):
            csv_data.append([f"Recommendation {i}", recommendation])
        
        # Convert to CSV string
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerows(csv_data)
        csv_str = output.getvalue()
        
        if output_path:
            with open(output_path, 'w', newline='') as f:
                f.write(csv_str)
            return "CSV saved to file"
        else:
            return csv_str
    
    def _export_excel_report(self, report: ComplianceReport, output_path: Optional[str] = None) -> bytes:
        """Export report as Excel"""
        
        # Create Excel data
        excel_data = {
            'Report Metadata': [
                ['Title', report.title],
                ['System ID', report.system_id],
                ['Framework', report.framework],
                ['Report Type', report.report_type],
                ['Generated At', report.generated_at.strftime('%Y-%m-%d %H:%M:%S')],
                ['Generated By', report.generated_by]
            ],
            'Summary': [[key, str(value)] for key, value in report.summary.items()],
            'Findings': [
                ['Title', 'Description', 'Evidence']
            ] + [[
                finding.get('title', ''),
                finding.get('description', ''),
                finding.get('evidence', '')
            ] for finding in report.findings],
            'Recommendations': [
                [f"Recommendation {i}", recommendation]
                for i, recommendation in enumerate(report.recommendations, 1)
            ]
        }
        
        # Create Excel file
        if output_path:
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                for sheet_name, data in excel_data.items():
                    df = pd.DataFrame(data[1:], columns=data[0] if data else [])
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            return b"Excel saved to file"
        else:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                for sheet_name, data in excel_data.items():
                    df = pd.DataFrame(data[1:], columns=data[0] if data else [])
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            buffer.seek(0)
            return buffer.getvalue()
    
    def _export_html_report(self, report: ComplianceReport, output_path: Optional[str] = None) -> str:
        """Export report as HTML"""
        
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{report.title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                h1 {{ color: #333; text-align: center; }}
                h2 {{ color: #666; border-bottom: 2px solid #666; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .metadata {{ background-color: #f9f9f9; padding: 15px; border-radius: 5px; }}
                .finding {{ margin: 15px 0; padding: 10px; border-left: 4px solid #007acc; }}
                .recommendation {{ margin: 10px 0; padding: 8px; background-color: #e8f4fd; }}
            </style>
        </head>
        <body>
            <h1>{report.title}</h1>
            
            <div class="metadata">
                <h2>Report Information</h2>
                <table>
                    <tr><td><strong>System ID</strong></td><td>{report.system_id}</td></tr>
                    <tr><td><strong>Framework</strong></td><td>{report.framework}</td></tr>
                    <tr><td><strong>Report Type</strong></td><td>{report.report_type}</td></tr>
                    <tr><td><strong>Generated At</strong></td><td>{report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}</td></tr>
                    <tr><td><strong>Generated By</strong></td><td>{report.generated_by}</td></tr>
                </table>
            </div>
            
            <h2>Summary</h2>
            <table>
        """
        
        for key, value in report.summary.items():
            html_template += f"<tr><td><strong>{key}</strong></td><td>{value}</td></tr>"
        
        html_template += """
            </table>
            
            <h2>Findings</h2>
        """
        
        for finding in report.findings:
            html_template += f"""
            <div class="finding">
                <h3>{finding.get('title', 'Finding')}</h3>
                <p>{finding.get('description', '')}</p>
                {f"<p><strong>Evidence:</strong> {finding.get('evidence', '')}</p>" if finding.get('evidence') else ''}
            </div>
            """
        
        html_template += """
            <h2>Recommendations</h2>
        """
        
        for i, recommendation in enumerate(report.recommendations, 1):
            html_template += f'<div class="recommendation">{i}. {recommendation}</div>'
        
        html_template += """
        </body>
        </html>
        """
        
        if output_path:
            with open(output_path, 'w') as f:
                f.write(html_template)
            return "HTML saved to file"
        else:
            return html_template
    
    def get_evidence_by_system(self, system_id: str, framework: str = None) -> List[EvidenceItem]:
        """Get evidence items for a system"""
        evidence = [item for item in self.evidence_items.values() 
                   if item.system_id == system_id]
        
        if framework:
            evidence = [item for item in evidence if item.framework == framework]
        
        return evidence
    
    def get_evidence_by_control(self, control_id: str) -> List[EvidenceItem]:
        """Get evidence items for a specific control"""
        return [item for item in self.evidence_items.values() 
                if item.control_id == control_id]
    
    def get_expired_evidence(self) -> List[EvidenceItem]:
        """Get expired evidence items"""
        now = datetime.now()
        return [item for item in self.evidence_items.values() 
                if item.expires_at and item.expires_at < now]
    
    def cleanup_expired_evidence(self) -> int:
        """Clean up expired evidence items"""
        expired_items = self.get_expired_evidence()
        
        for item in expired_items:
            # Remove from collections
            for collection in self.evidence_collections.values():
                if item.id in collection.evidence_items:
                    collection.evidence_items.remove(item.id)
            
            # Remove evidence item
            del self.evidence_items[item.id]
        
        if expired_items:
            self._save_evidence_metadata()
        
        logger.info(f"Cleaned up {len(expired_items)} expired evidence items")
        return len(expired_items)
    
    def get_evidence_statistics(self) -> Dict[str, Any]:
        """Get evidence collection statistics"""
        total_items = len(self.evidence_items)
        total_collections = len(self.evidence_collections)
        total_reports = len(self.compliance_reports)
        
        # Count by type
        type_counts = {}
        for item in self.evidence_items.values():
            type_name = item.evidence_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
        
        # Count by status
        status_counts = {}
        for item in self.evidence_items.values():
            status_name = item.status.value
            status_counts[status_name] = status_counts.get(status_name, 0) + 1
        
        # Count by framework
        framework_counts = {}
        for item in self.evidence_items.values():
            framework_name = item.framework
            framework_counts[framework_name] = framework_counts.get(framework_name, 0) + 1
        
        return {
            "total_evidence_items": total_items,
            "total_collections": total_collections,
            "total_reports": total_reports,
            "evidence_by_type": type_counts,
            "evidence_by_status": status_counts,
            "evidence_by_framework": framework_counts,
            "expired_items": len(self.get_expired_evidence())
        }

