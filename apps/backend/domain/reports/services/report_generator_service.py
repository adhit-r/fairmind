"""
Report Generator Service

Generates professional PDF reports for bias audits, compliance certificates, and model cards.
"""

import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import uuid

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.units import inch

logger = logging.getLogger(__name__)

class ReportGeneratorService:
    """
    Service for generating PDF reports.
    """
    
    def __init__(self):
        self.output_dir = Path("uploads/reports")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        
    def _setup_custom_styles(self):
        """Define custom paragraph styles"""
        self.styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1  # Center
        ))
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.HexColor('#1a365d')
        ))
        self.styles.add(ParagraphStyle(
            name='MetricValue',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#2d3748')
        ))

    async def generate_bias_audit_report(self, model_data: Dict[str, Any], bias_results: Dict[str, Any]) -> str:
        """
        Generate a Bias Audit Report PDF.
        
        Args:
            model_data: Dictionary containing model metadata.
            bias_results: Dictionary containing bias analysis results.
            
        Returns:
            Path to the generated PDF file.
        """
        filename = f"bias_audit_{model_data.get('name', 'model')}_{datetime.now().strftime('%Y%m%d')}.pdf"
        filepath = self.output_dir / filename
        
        doc = SimpleDocTemplate(str(filepath), pagesize=letter)
        story = []
        
        # Title
        story.append(Paragraph("Bias Audit Report", self.styles['ReportTitle']))
        story.append(Spacer(1, 0.25*inch))
        
        # Model Info
        story.append(Paragraph("Model Information", self.styles['SectionHeader']))
        data = [
            ["Model Name", model_data.get("name", "N/A")],
            ["Version", model_data.get("version", "N/A")],
            ["Author", model_data.get("author", "N/A")],
            ["Date", datetime.now().strftime("%Y-%m-%d")]
        ]
        t = Table(data, colWidths=[2*inch, 4*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#edf2f7')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        story.append(t)
        
        # Executive Summary
        story.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        overall_score = bias_results.get("overall_score", 0)
        status = "PASS" if overall_score >= 0.8 else "NEEDS REVIEW"
        color = "green" if status == "PASS" else "red"
        
        summary_text = f"""
        This report summarizes the bias evaluation for <b>{model_data.get('name')}</b>. 
        The model achieved an overall fairness score of <b>{overall_score:.2f}</b>.
        Based on established thresholds, the model status is: <font color='{color}'><b>{status}</b></font>.
        """
        story.append(Paragraph(summary_text, self.styles['Normal']))
        
        # Detailed Metrics
        story.append(Paragraph("Detailed Metrics", self.styles['SectionHeader']))
        
        metrics_data = [["Metric", "Score", "Threshold", "Status"]]
        for metric, value in bias_results.get("metrics", {}).items():
            status = "Pass" if value < 0.1 else "Fail" # Assuming lower is better for bias metrics
            metrics_data.append([
                metric.replace("_", " ").title(),
                f"{value:.3f}",
                "0.100",
                status
            ])
            
        t = Table(metrics_data, colWidths=[2.5*inch, 1*inch, 1*inch, 1*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2b6cb0')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(t)
        
        # Recommendations
        story.append(Paragraph("Recommendations", self.styles['SectionHeader']))
        recommendations = bias_results.get("recommendations", ["No specific recommendations."])
        for rec in recommendations:
            story.append(Paragraph(f"• {rec}", self.styles['Normal']))
            
        doc.build(story)
        logger.info(f"Generated Bias Audit Report: {filepath}")
        return str(filepath)

    async def generate_compliance_certificate(self, model_data: Dict[str, Any], compliance_data: Dict[str, Any]) -> str:
        """
        Generate a Compliance Certificate PDF.
        
        Args:
            model_data: Dictionary containing model metadata.
            compliance_data: Dictionary containing compliance status and requirements.
            
        Returns:
            Path to the generated PDF file.
        """
        filename = f"compliance_cert_{model_data.get('name', 'model')}_{datetime.now().strftime('%Y%m%d')}.pdf"
        filepath = self.output_dir / filename
        
        doc = SimpleDocTemplate(str(filepath), pagesize=letter)
        story = []
        
        # Title
        story.append(Paragraph("Certificate of Compliance", self.styles['ReportTitle']))
        story.append(Spacer(1, 0.5*inch))
        
        # Certification Text
        cert_text = f"""
        This document certifies that the model <b>{model_data.get('name')}</b> (Version {model_data.get('version')})
        has been evaluated against the <b>{compliance_data.get('framework', 'Standard AI')}</b> framework.
        """
        story.append(Paragraph(cert_text, self.styles['Normal']))
        story.append(Spacer(1, 0.25*inch))
        
        # Status
        status = compliance_data.get("status", "Pending")
        story.append(Paragraph(f"Compliance Status: <b>{status}</b>", self.styles['Heading3']))
        
        # Requirements Checklist
        story.append(Paragraph("Requirements Checklist", self.styles['SectionHeader']))
        
        req_data = [["Requirement", "Status", "Evidence"]]
        for req in compliance_data.get("requirements", []):
            req_data.append([
                req.get("name", "Unknown"),
                req.get("status", "Pending"),
                "Verified" if req.get("evidence") else "Missing"
            ])
            
        t = Table(req_data, colWidths=[3.5*inch, 1*inch, 1.5*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2f855a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(t)
        
        # Signature
        story.append(Spacer(1, 1*inch))
        story.append(Paragraph("_" * 30, self.styles['Normal']))
        story.append(Paragraph("Authorized Signature", self.styles['Normal']))
        story.append(Paragraph(f"Date: {datetime.now().strftime('%Y-%m-%d')}", self.styles['Normal']))
        
        doc.build(story)
        logger.info(f"Generated Compliance Certificate: {filepath}")
    async def generate_model_card(self, model_data: Dict[str, Any], card_data: Dict[str, Any]) -> str:
        """
        Generate a Model Card PDF.
        
        Args:
            model_data: Dictionary containing model metadata.
            card_data: Dictionary containing model card specific details.
            
        Returns:
            Path to the generated PDF file.
        """
        filename = f"model_card_{model_data.get('name', 'model')}_{datetime.now().strftime('%Y%m%d')}.pdf"
        filepath = self.output_dir / filename
        
        doc = SimpleDocTemplate(str(filepath), pagesize=letter)
        story = []
        
        # Title
        story.append(Paragraph("Model Card", self.styles['ReportTitle']))
        story.append(Spacer(1, 0.25*inch))
        
        # 1. Model Details
        story.append(Paragraph("1. Model Details", self.styles['SectionHeader']))
        details_data = [
            ["Name", model_data.get("name", "N/A")],
            ["Version", model_data.get("version", "N/A")],
            ["Date", datetime.now().strftime("%Y-%m-%d")],
            ["License", card_data.get("license", "Proprietary")],
            ["Model Type", model_data.get("model_type", "N/A")]
        ]
        t = Table(details_data, colWidths=[2*inch, 4*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#edf2f7')),
            ('GRID', (0, 0), (-1, -1), 1, colors.white),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ]))
        story.append(t)
        
        # 2. Intended Use
        story.append(Paragraph("2. Intended Use", self.styles['SectionHeader']))
        story.append(Paragraph("<b>Primary Uses:</b>", self.styles['Normal']))
        story.append(Paragraph(card_data.get("intended_use", "Not specified"), self.styles['Normal']))
        story.append(Spacer(1, 0.1*inch))
        story.append(Paragraph("<b>Out-of-Scope Uses:</b>", self.styles['Normal']))
        story.append(Paragraph(card_data.get("out_of_scope", "Not specified"), self.styles['Normal']))
        
        # 3. Factors
        story.append(Paragraph("3. Factors", self.styles['SectionHeader']))
        story.append(Paragraph("<b>Relevant Factors:</b> " + card_data.get("factors", "Demographic groups, environmental conditions"), self.styles['Normal']))
        
        # 4. Metrics
        story.append(Paragraph("4. Metrics", self.styles['SectionHeader']))
        metrics = card_data.get("metrics", {})
        if metrics:
            metric_data = [["Metric", "Value"]]
            for k, v in metrics.items():
                metric_data.append([k, str(v)])
            t = Table(metric_data, colWidths=[3*inch, 3*inch])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a5568')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            story.append(t)
        else:
            story.append(Paragraph("No metrics provided.", self.styles['Normal']))
            
        # 5. Ethical Considerations
        story.append(Paragraph("5. Ethical Considerations", self.styles['SectionHeader']))
        story.append(Paragraph(card_data.get("ethical_considerations", "None specified"), self.styles['Normal']))
        
        doc.build(story)
        logger.info(f"Generated Model Card: {filepath}")
        return str(filepath)

# Singleton instance
report_generator_service = ReportGeneratorService()
