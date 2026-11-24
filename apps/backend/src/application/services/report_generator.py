"""
Report Generator Service
Generates PDF and DOCX reports for bias evaluations, compliance assessments, and governance audits.
"""

from io import BytesIO
from xml.sax.saxutils import escape
from datetime import datetime
from typing import Optional, List, Dict, Any

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

from src.application.services.system_assurance_report import REPORT_TYPE as SYSTEM_ASSURANCE_REPORT


# ─── Data Models ────────────────────────────────────────────────────────────

class ComplianceStatus:
    def __init__(
        self,
        gdpr_compliant: bool = False,
        ai_act_compliant: bool = False,
        fairness_score: Optional[float] = None,
    ):
        self.gdpr_compliant = gdpr_compliant
        self.ai_act_compliant = ai_act_compliant
        self.fairness_score = fairness_score


class EvaluationSummary:
    def __init__(
        self,
        total_tests: int,
        tests_passed: int,
        tests_failed: int,
        overall_bias_rate: float,
        evaluation_time: Optional[str] = None,
    ):
        self.total_tests = total_tests
        self.tests_passed = tests_passed
        self.tests_failed = tests_failed
        self.overall_bias_rate = overall_bias_rate
        self.evaluation_time = evaluation_time


class BiasReportData:
    def __init__(
        self,
        timestamp: str,
        model_type: str,
        model_description: Optional[str] = None,
        evaluation_summary: Optional[EvaluationSummary] = None,
        overall_risk: str = "medium",
        risk_factors: Optional[List[str]] = None,
        recommendations: Optional[List[str]] = None,
        compliance_status: Optional[ComplianceStatus] = None,
        explainability_insights: Optional[List[str]] = None,
    ):
        self.timestamp = timestamp
        self.model_type = model_type
        self.model_description = model_description
        self.evaluation_summary = evaluation_summary
        self.overall_risk = overall_risk
        self.risk_factors = risk_factors or []
        self.recommendations = recommendations or []
        self.compliance_status = compliance_status
        self.explainability_insights = explainability_insights or []


# ─── ReportLab PDF Generator ────────────────────────────────────────────────

class PDFReportGenerator:
    """Generate professional PDF reports using ReportLab."""

    COLORS = {
        "low": colors.HexColor("#22c55e"),
        "medium": colors.HexColor("#eab308"),
        "high": colors.HexColor("#f97316"),
        "critical": colors.HexColor("#ef4444"),
        "primary": colors.HexColor("#1f2937"),
        "accent": colors.HexColor("#ff6b35"),
        "text": colors.HexColor("#111827"),
        "muted": colors.HexColor("#6b7280"),
    }

    def generate(self, data: BiasReportData) -> bytes:
        """Generate PDF report and return as bytes."""
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
        )

        # Build content
        story = []
        styles = self._get_styles()

        # Header
        story.extend(self._build_header(styles, data))

        # Executive Summary
        story.append(Spacer(1, 0.3 * inch))
        story.extend(self._build_executive_summary(styles, data))

        # Evaluation Summary
        story.append(PageBreak())
        story.extend(self._build_evaluation_summary(styles, data))

        # Compliance Status
        story.append(Spacer(1, 0.3 * inch))
        story.extend(self._build_compliance_status(styles, data))

        # Risk Factors
        if data.risk_factors:
            story.append(Spacer(1, 0.3 * inch))
            story.extend(self._build_risk_factors(styles, data))

        # Recommendations
        story.append(Spacer(1, 0.3 * inch))
        story.extend(self._build_recommendations(styles, data))

        # Footer
        story.append(Spacer(1, 0.5 * inch))
        story.extend(self._build_footer(styles, data))

        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

    def _get_styles(self):
        """Get or create document styles."""
        styles = getSampleStyleSheet()

        # Title
        styles.add(
            ParagraphStyle(
                name="CustomTitle",
                parent=styles["Heading1"],
                fontSize=28,
                textColor=self.COLORS["primary"],
                spaceAfter=6,
                fontName="Helvetica-Bold",
            )
        )

        # Heading
        styles.add(
            ParagraphStyle(
                name="CustomHeading",
                parent=styles["Heading2"],
                fontSize=14,
                textColor=self.COLORS["primary"],
                spaceAfter=12,
                fontName="Helvetica-Bold",
                borderPadding=12,
                backColor=colors.HexColor("#f3f4f6"),
            )
        )

        # Body
        styles.add(
            ParagraphStyle(
                name="CustomBody",
                parent=styles["BodyText"],
                fontSize=10,
                textColor=self.COLORS["text"],
                spaceAfter=12,
            )
        )

        return styles

    def _build_header(self, styles, data):
        """Build report header with FairMind branding."""
        elements = []
        elements.append(Paragraph("FairMind", styles["CustomTitle"]))
        elements.append(
            Paragraph(
                "AI Governance & Bias Detection Platform",
                styles["Normal"],
            )
        )
        elements.append(Paragraph("Bias Evaluation Report", styles["Heading2"]))
        elements.append(
            Paragraph(
                f"Generated: {datetime.fromisoformat(data.timestamp).strftime('%B %d, %Y at %H:%M UTC')}",
                styles["Normal"],
            )
        )
        return elements

    def _build_executive_summary(self, styles, data):
        """Build executive summary section."""
        elements = []
        elements.append(Paragraph("Executive Summary", styles["CustomHeading"]))

        # Risk level
        risk_color = self.COLORS.get(data.overall_risk, self.COLORS["medium"])
        elements.append(
            Paragraph(
                f"<b>Overall Risk Level:</b> <font color='{risk_color.hexval()}'>{data.overall_risk.upper()}</font>",
                styles["Normal"],
            )
        )

        # Key metrics
        if data.evaluation_summary:
            bias_rate = (data.evaluation_summary.overall_bias_rate * 100)
            pass_rate = (data.evaluation_summary.tests_passed / max(1, data.evaluation_summary.total_tests)) * 100
            elements.append(
                Paragraph(
                    f"<b>Bias Rate:</b> {bias_rate:.1f}% | <b>Tests Passed:</b> {data.evaluation_summary.tests_passed}/{data.evaluation_summary.total_tests} ({pass_rate:.0f}%)",
                    styles["Normal"],
                )
            )

        return elements

    def _build_evaluation_summary(self, styles, data):
        """Build evaluation summary table."""
        elements = []
        elements.append(Paragraph("Evaluation Summary", styles["CustomHeading"]))

        if data.evaluation_summary:
            table_data = [
                ["Metric", "Value"],
                ["Total Tests", str(data.evaluation_summary.total_tests)],
                ["Tests Passed", str(data.evaluation_summary.tests_passed)],
                ["Tests Failed", str(data.evaluation_summary.tests_failed)],
                ["Overall Bias Rate", f"{data.evaluation_summary.overall_bias_rate * 100:.1f}%"],
            ]

            table = Table(table_data, colWidths=[2.5 * inch, 2.5 * inch])
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), self.COLORS["primary"]),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 12),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                        ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9fafb")]),
                    ]
                )
            )
            elements.append(table)

        return elements

    def _build_compliance_status(self, styles, data):
        """Build compliance status section."""
        elements = []
        elements.append(Paragraph("Compliance Status", styles["CustomHeading"]))

        if data.compliance_status:
            gdpr_status = "✓ COMPLIANT" if data.compliance_status.gdpr_compliant else "✗ NON-COMPLIANT"
            ai_act_status = "✓ COMPLIANT" if data.compliance_status.ai_act_compliant else "✗ NON-COMPLIANT"

            elements.append(Paragraph(f"<b>GDPR:</b> {gdpr_status}", styles["Normal"]))
            elements.append(Paragraph(f"<b>EU AI Act:</b> {ai_act_status}", styles["Normal"]))

            if data.compliance_status.fairness_score:
                elements.append(
                    Paragraph(
                        f"<b>Fairness Score:</b> {data.compliance_status.fairness_score * 100:.1f}%",
                        styles["Normal"],
                    )
                )

        return elements

    def _build_risk_factors(self, styles, data):
        """Build risk factors section."""
        elements = []
        elements.append(Paragraph("Identified Risk Factors", styles["CustomHeading"]))

        for i, factor in enumerate(data.risk_factors, 1):
            elements.append(Paragraph(f"<b>{i}.</b> {factor}", styles["Normal"]))

        return elements

    def _build_recommendations(self, styles, data):
        """Build recommendations section."""
        elements = []
        elements.append(Paragraph("Recommendations", styles["CustomHeading"]))

        for i, rec in enumerate(data.recommendations, 1):
            elements.append(Paragraph(f"<b>{i}.</b> {rec}", styles["Normal"]))

        return elements

    def _build_footer(self, styles, data):
        """Build report footer."""
        elements = []
        elements.append(
            Paragraph(
                "This report was generated by FairMind AI Governance Platform.",
                styles["Normal"],
            )
        )
        elements.append(
            Paragraph(f"Report ID: {data.timestamp.replace(':', '').replace('-', '')}",
                      styles["Normal"])
        )
        return elements


# ─── Python-DOCX DOCX Generator ─────────────────────────────────────────────

class DOCXReportGenerator:
    """Generate professional DOCX reports using python-docx."""

    def generate(self, data: BiasReportData) -> bytes:
        """Generate DOCX report and return as bytes."""
        doc = Document()

        # Set up document margins
        sections = doc.sections
        for section in sections:
            section.top_margin = Inches(0.75)
            section.bottom_margin = Inches(0.75)
            section.left_margin = Inches(0.75)
            section.right_margin = Inches(0.75)

        # Header
        self._add_header(doc, data)

        # Executive Summary
        self._add_executive_summary(doc, data)

        # Evaluation Summary
        self._add_evaluation_summary(doc, data)

        # Compliance Status
        self._add_compliance_status(doc, data)

        # Risk Factors
        if data.risk_factors:
            self._add_risk_factors(doc, data)

        # Recommendations
        if data.recommendations:
            self._add_recommendations(doc, data)

        # Footer
        self._add_footer(doc, data)

        # Save to bytes
        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()

    def _add_header(self, doc, data):
        """Add header with FairMind branding."""
        title = doc.add_paragraph()
        title.style = "Heading 1"
        run = title.add_run("FairMind")
        run.font.size = Pt(28)
        run.font.bold = True
        run.font.color.rgb = RGBColor(31, 41, 55)

        subtitle = doc.add_paragraph("AI Governance & Bias Detection Platform")
        subtitle_run = subtitle.runs[0]
        subtitle_run.font.size = Pt(10)
        subtitle_run.font.color.rgb = RGBColor(107, 114, 128)

        report_title = doc.add_paragraph("Bias Evaluation Report")
        report_title.style = "Heading 2"

        gen_date = doc.add_paragraph(
            f"Generated: {datetime.fromisoformat(data.timestamp).strftime('%B %d, %Y at %H:%M UTC')}"
        )
        gen_date_run = gen_date.runs[0]
        gen_date_run.font.size = Pt(10)
        gen_date_run.font.color.rgb = RGBColor(107, 114, 128)

        doc.add_paragraph()  # Spacer

    def _add_executive_summary(self, doc, data):
        """Add executive summary."""
        heading = doc.add_paragraph("Executive Summary")
        heading.style = "Heading 2"

        risk_p = doc.add_paragraph()
        risk_p.add_run("Overall Risk Level: ").bold = True
        risk_run = risk_p.add_run(data.overall_risk.upper())
        risk_colors = {
            "low": RGBColor(34, 197, 94),
            "medium": RGBColor(234, 179, 8),
            "high": RGBColor(249, 115, 22),
            "critical": RGBColor(239, 68, 68),
        }
        risk_run.font.color.rgb = risk_colors.get(data.overall_risk, RGBColor(107, 114, 128))
        risk_run.font.bold = True

        if data.evaluation_summary:
            bias_rate = data.evaluation_summary.overall_bias_rate * 100
            pass_rate = (data.evaluation_summary.tests_passed / max(1, data.evaluation_summary.total_tests)) * 100
            metrics = doc.add_paragraph(
                f"Bias Rate: {bias_rate:.1f}% | Tests Passed: {data.evaluation_summary.tests_passed}/{data.evaluation_summary.total_tests} ({pass_rate:.0f}%)"
            )
            metrics_run = metrics.runs[0]
            metrics_run.font.size = Pt(10)

        doc.add_paragraph()  # Spacer

    def _add_evaluation_summary(self, doc, data):
        """Add evaluation summary table."""
        heading = doc.add_paragraph("Evaluation Summary")
        heading.style = "Heading 2"

        if data.evaluation_summary:
            table = doc.add_table(rows=5, cols=2)
            table.style = "Light Grid Accent 1"

            # Header row
            table.cell(0, 0).text = "Metric"
            table.cell(0, 1).text = "Value"

            # Data rows
            table.cell(1, 0).text = "Total Tests"
            table.cell(1, 1).text = str(data.evaluation_summary.total_tests)

            table.cell(2, 0).text = "Tests Passed"
            table.cell(2, 1).text = str(data.evaluation_summary.tests_passed)

            table.cell(3, 0).text = "Tests Failed"
            table.cell(3, 1).text = str(data.evaluation_summary.tests_failed)

            table.cell(4, 0).text = "Overall Bias Rate"
            table.cell(4, 1).text = f"{data.evaluation_summary.overall_bias_rate * 100:.1f}%"

        doc.add_paragraph()  # Spacer

    def _add_compliance_status(self, doc, data):
        """Add compliance status."""
        heading = doc.add_paragraph("Compliance Status")
        heading.style = "Heading 2"

        if data.compliance_status:
            gdpr_p = doc.add_paragraph()
            gdpr_p.add_run("GDPR: ").bold = True
            gdpr_status = "✓ COMPLIANT" if data.compliance_status.gdpr_compliant else "✗ NON-COMPLIANT"
            gdpr_p.add_run(gdpr_status)

            ai_act_p = doc.add_paragraph()
            ai_act_p.add_run("EU AI Act: ").bold = True
            ai_act_status = "✓ COMPLIANT" if data.compliance_status.ai_act_compliant else "✗ NON-COMPLIANT"
            ai_act_p.add_run(ai_act_status)

            if data.compliance_status.fairness_score:
                fairness_p = doc.add_paragraph()
                fairness_p.add_run("Fairness Score: ").bold = True
                fairness_p.add_run(f"{data.compliance_status.fairness_score * 100:.1f}%")

        doc.add_paragraph()  # Spacer

    def _add_risk_factors(self, doc, data):
        """Add risk factors."""
        heading = doc.add_paragraph("Identified Risk Factors")
        heading.style = "Heading 2"

        for i, factor in enumerate(data.risk_factors, 1):
            p = doc.add_paragraph(factor, style="List Number")

        doc.add_paragraph()  # Spacer

    def _add_recommendations(self, doc, data):
        """Add recommendations."""
        heading = doc.add_paragraph("Recommendations")
        heading.style = "Heading 2"

        for i, rec in enumerate(data.recommendations, 1):
            p = doc.add_paragraph(rec, style="List Number")

        doc.add_paragraph()  # Spacer

    def _add_footer(self, doc, data):
        """Add footer."""
        footer_para = doc.add_paragraph("This report was generated by FairMind AI Governance Platform.")
        footer_run = footer_para.runs[0]
        footer_run.font.size = Pt(9)
        footer_run.font.color.rgb = RGBColor(107, 114, 128)

        report_id = doc.add_paragraph(f"Report ID: {data.timestamp.replace(':', '').replace('-', '')}")
        report_id_run = report_id.runs[0]
        report_id_run.font.size = Pt(9)
        report_id_run.font.color.rgb = RGBColor(107, 114, 128)


# ─── Report Service (Facade) ────────────────────────────────────────────────

class ReportGenerator:
    """Facade for report generation (PDF and DOCX)."""

    def __init__(self):
        self.pdf_gen = PDFReportGenerator()
        self.docx_gen = DOCXReportGenerator()

    def generate_pdf(self, data: BiasReportData) -> bytes:
        """Generate PDF report."""
        return self.pdf_gen.generate(data)

    def generate_docx(self, data: BiasReportData) -> bytes:
        """Generate DOCX report."""
        return self.docx_gen.generate(data)


# ─── Stored snapshot export ─────────────────────────────────────────────────

def _snapshot_sections(report: Dict[str, Any], content_hash: str) -> List[tuple]:
    """Lay a stored audit-report snapshot out as (heading, header_row | None, rows) sections."""
    data = report.get("data") or {}
    system = data.get("system") or {}
    gate = data.get("gate") or {}
    s = lambda v: "" if v is None else str(v)  # noqa: E731
    sections = [
        ("Record", None, [
            ("Report ID", report["id"]),
            ("Created at", s(report.get("createdAt"))),
            ("Report type", s(report.get("reportType"))),
            ("Generated by", s(report.get("generatedBy"))),
            ("Snapshot SHA-256", content_hash),
        ]),
        ("System", None, [
            ("Name", s(system.get("name"))),
            ("System ID", s(system.get("id") or report.get("systemId"))),
            ("Owner", s(system.get("owner"))),
            ("Risk tier", s(system.get("riskTier"))),
            ("Lifecycle stage", s(system.get("lifecycleStage"))),
        ]),
        ("Gate", None, [("Verdict", s(gate.get("verdict")))] + [("Reason", s(r)) for r in gate.get("reasons") or []]),
    ]
    tables = (
        ("Risks", ("Title", "Severity", "Status"), "risks", ("title", "severity", "status")),
        ("Evidence", ("Title", "Type", "Status"), "evidence", ("title", "type", "status")),
        ("Remediation", ("Title", "Priority", "Status", "Owner"), "remediation", ("title", "priority", "status", "owner")),
        ("Approvals", ("Status", "Requested by", "Created at"), "approvals", ("status", "requestedBy", "createdAt")),
    )
    for heading, head, key, fields in tables:
        sections.append((heading, head, [tuple(s(item.get(f)) for f in fields) for item in data.get(key) or []]))
    return sections


# ─── Role reports (Reports page) ─────────────────────────────────────────────

READINESS_WORDS = {"met": "Met", "progress": "In progress", "attention": "Needs attention", "notstarted": "Not started"}
_CELL_WORDS = {"proven": "Proven", "attested": "Attested", "excluded": "Excluded", "partial": "Partial", "estimated": "Estimated",
               "planned": "Planned", "atorg": "At organisation", "fails": "Failing", "stale": "Stale", "open": "Open", "none": "Not tracked"}


def _role_sections(report: Dict[str, Any], content_hash: str) -> List[tuple]:
    """A sealed role report as (heading, header_row | None, rows): every figure read from the stored model."""
    m = report.get("data") or {}
    s = lambda v: "" if v is None else str(v)  # noqa: E731
    scope = (m.get("scope") or {}).get("systemName") or "Whole organisation"
    fw = (m.get("framework") or {}).get("name") or "No framework followed"
    out: List[tuple] = [("Record", None, [
        ("Report ID", report["id"]), ("Reader", s(m.get("role")).capitalize()), ("Scope", scope), ("Framework", fw),
        ("Computed at", s(m.get("generatedAt"))), ("Approved by", s(report.get("approvedBy") or report.get("generatedBy"))),
        ("Approved at", s(report.get("approvedAt") or report.get("createdAt"))), ("Seal SHA-256", content_hash),
    ])]
    if r := m.get("readiness"):
        out.append(("Readiness", None, [(READINESS_WORDS[k], s(r[k])) for k in READINESS_WORDS] + [("Requirement cells", s(r["total"])), ("Share met", f"{r['pct']}%")]))
    if road := m.get("road"):
        rows = [(x["action"] or x["check"] or "", x["systemName"], f"{len(x['closes'])}: {', '.join(x['closes'][:4])}", f"+{x['gain']}", s(x.get("owner") or "Unassigned")) for x in road["steps"]]
        out.append(("Road to the audit", ("Step", "System", "Closes", "Points", "Owner"), rows + [("Forecast if every step is done", "", "", f"{road['forecast']}%", "")]))
    if p := m.get("proof"):
        out.append(("Proof depth", ("System", "Measured", "Tool estimate", "Attested", "No proof"),
                    [(x["name"], s(x["measured"]), s(x["estimated"]), s(x["attested"]), s(x["none"])) for x in p["bySystem"]]
                    + [("All in scope", s(p["measured"]), s(p["estimated"]), s(p["attested"]), s(p["none"]))]))
    if g := m.get("governed"):
        out.append(("Governed AI", None, [("Found", s(g["found"])), ("Registered", s(g["registered"])), ("Checked", s(g["checked"])), ("Approved", s(g["approved"]))]
                    + [("Not registered", f"{a['name']} ({a['kind']}, {a['source']})") for a in g["unregistered"]]))
    if o := m.get("oversight"):
        wait = o["medianWaitHours"] if o["medianWaitHours"] is not None else "No decisions"
        out.append(("Agents and people, last 30 days", None, [("Agent steps", s(o["agentSteps"])), ("Decisions by people", s(o["decisions"])),
                    ("Median wait at a gate (hours)", s(wait)), ("Approved without a named person", s(o["approvedWithoutPerson"]))]))
    if (d := m.get("decisions")) is not None:
        out.append(("Waiting for a decision", ("System", "Requested by", "Days waiting"), [(x["systemName"], s(x["requestedBy"]), s(x["waitingDays"])) for x in d]))
    if c := m.get("crosswalk"):
        out.append(("Coverage through the clause map", ("Framework", "Followed", "Covered"), [(x["name"], "Yes" if x["followed"] else "No", f"{x['coverage']}%") for x in c["frameworks"]]))
    if t := m.get("tasks"):
        out.append(("Open work by owner", ("Owner", "On time", "Overdue"), [(x["owner"], s(x["onTime"]), s(x["overdue"])) for x in t["byOwner"]]))
        out.append(("Overdue tasks", ("Task", "Requirement", "Owner", "Days late"), [(x["title"], s(x["subject"]), x["owner"], s(x["daysLate"])) for x in t["overdueList"]]))
    if gr := m.get("grid"):
        names = [x["name"] for x in gr["systems"]]
        out.append(("Where systems fall short", ("Requirement", *names), [(f"{x['control']} {x['title']}", *[_CELL_WORDS.get(c, c) for c in x["cells"]]) for x in gr["requirements"]]))
    if (sy := m.get("systems")) is not None:
        out.append(("Release gate", ("System", "Verdict", "Checks"),
                    [(x["name"], s(x["verdict"]), "; ".join(f"{c['label']}: {'failing' if c['fails'] else c['state']}" for c in x["checks"])) for x in sy]))
    if e := m.get("engineering"):
        out.append(("Agent tools", ("System", "Tool", "Policy", "A person approves"), [(x["systemName"], x["tool"], s(x["policy"]), "Yes" if x["gated"] else "No") for x in e["toolExposure"]]))
        out.append(("Fairness over time", ("System", "Latest disparate impact", "Limit", "Runs"),
                    [(x["systemName"], s(x["points"][-1]["value"]), s(x["threshold"]), s(len(x["points"]))) for x in e["fairnessDrift"]]))
        out.append(("Fixes to make", ("Fix", "System", "Priority", "Status"), [(x["title"], x["systemName"], s(x["priority"]), s(x["status"])) for x in e["fixes"]]))
    if a := m.get("auditor"):
        led = a["ledger"]
        out.append(("Ledger chains", ("Chain", "Chains", "Entries", "Broken"),
                    [(x["kind"], s(x["chains"]), s(x["entries"] if x["entries"] is not None else ""), s(x["broken"])) for x in led["chains"]]))
        out.append(("Audit sample", ("Evidence", "Type", "Provenance", "System"),
                    [(x["title"], s(x["type"]), s(x["provenance"]), x["systemName"]) for x in a["sample"]["items"]] + [("Seed", s(a["sample"]["seed"]), "", "")]))
        if soa := a.get("soa"):
            out.append((f"Statement of applicability: {soa['systemName']}", ("Clause", "Title", "State", "Applicability", "Justification"),
                        [(x["control"], x["title"], READINESS_WORDS.get(x["readiness"], x["readiness"]), s(x.get("applicability")), s(x.get("justification"))) for x in soa["controls"]]))
        out.append(("Inspection packs", ("Pack", "Created", "Manifest SHA-256"), [(x["title"], s(x["createdAt"]), s(x["manifestHash"])) for x in a["packs"]]))
    if rk := m.get("risk"):
        out.append(("Risk register", ("Risk", "System", "Severity", "Likelihood", "Status", "Owner"),
                    [(x["title"], x["systemName"], s(x["severity"]), s(x["likelihood"]), s(x["status"]), s(x.get("owner"))) for x in rk["risks"]]))
        out.append(("Acceptance waiting for a second person", ("Risk", "System", "Owner", "Days waiting"),
                    [(x["title"], x["systemName"], s(x.get("owner")), s(x.get("waitingDays"))) for x in rk["acceptanceWaiting"]]))
    return out


def _is_role(report: Dict[str, Any]) -> bool:
    return str(report.get("reportType") or "").startswith("role:")


def _system_assurance_sections(report: Dict[str, Any], content_hash: str) -> List[tuple]:
    data, config = report["data"], report["config"]
    system, framework, period, coverage = (data[key] for key in ("system", "framework", "period", "coverage"))
    sections = [
        ("Record", None, [
            ("Report ID", report["id"]), ("Template version", str(config["templateVersion"])),
            ("Previewed at", data["generatedAt"]), ("Approved by", report["approvedBy"]),
            ("Approved at", report["approvedAt"]), ("Revision SHA-256", content_hash),
        ]),
        ("Scope", None, [
            ("System", system["name"]), ("System ID", system["id"]),
            ("System version", system.get("version") or "Not recorded"),
            ("Owner", system["owner"] or "Unassigned"), ("Risk tier", system["riskTier"]),
            ("Lifecycle stage at preview", system["lifecycleStage"]),
            ("Framework version", f"{framework['name']} {framework['versionLabel']}"),
            ("Framework version ID", framework["versionId"]), ("Assignment ID", framework["assignmentId"]),
            ("Evidence period", f"{period['dateFrom']} to {period['dateTo']} ({period['timeZone']}, inclusive)"),
        ]),
        ("Evidence population", None, [
            ("Mapped runs in the period", str(coverage["evidenceRuns"])),
            ("Controls on the assignment", str(coverage["controls"])),
            ("Runs excluded without an assignment mapping", str(coverage["excludedUnmappedRuns"])),
            ("System runs excluded without a valid capture time", str(coverage["excludedUndatedRuns"])),
        ]),
        ("Limitations", None, [(value,) for value in data["limitations"]]),
        ("Unresolved system findings opened in the period", ("Finding", "Severity", "Status at preview", "Opened at", "Finding ID"), [
            (finding["title"], finding["severity"], finding["status"], finding["createdAt"], finding["id"])
            for finding in data["findings"]
        ]),
        ("Control state at preview", ("Control", "Applicability", "Assessment", "Passed, accepted mappings", "Evidence freshness"), [
            (f"{control['externalId']} {control['title']}", control["applicability"], control["status"],
             str(control["acceptedEvidenceCount"]), control["evidenceStatus"])
            for control in data["controls"]
        ]),
        ("Evidence runs in the period", ("Source", "Captured at", "Result", "Run ID"), [
            (f"{run['sourceType']} · {run['sourceIdentifier']}", run["capturedAt"], run["result"], run["runId"])
            for run in data["evidence"]
        ]),
    ]
    if config.get("definitionId"):
        sections[0][2].insert(1, ("Report definition ID", config["definitionId"]))
    control_by_id = {control["id"]: control for control in data["controls"]}
    for run in data["evidence"]:
        rows = [
            ("Run ID", run["runId"]), ("Evidence run record ID", run["id"]),
            ("Evidence artifact ID", run["evidenceId"] or "Not recorded"), ("Content SHA-256", run["contentHash"]),
            ("Assurance source", run["assuranceSource"] or "Not recorded"),
            ("Capability state", run["capabilityState"] or "Not recorded"),
            ("Subject version", run["subjectVersion"] or "Not recorded"),
            ("Expires at", run.get("expiresAt") or "Not recorded"),
        ]
        if run["sampleCount"] is not None:
            rows.append(("Sample count", str(run["sampleCount"])))
        rows += [("Run limitation", value) for value in run["limitations"]]
        rows += [("Scope exclusion", value) for value in run["scopeExclusions"]]
        for measurement in run["measurements"]:
            unit = f" {measurement['unit']}" if measurement.get("unit") else ""
            group = f" ({measurement['slice']})" if measurement.get("slice") else ""
            rows.append((f"{measurement['name']}{group}", f"{measurement['value']}{unit}"))
        for threshold in run["thresholds"]:
            unit = f" {threshold['unit']}" if threshold.get("unit") else ""
            rows.append((f"Threshold for {threshold['metric']}", f"{threshold['operator']} {threshold['value']}{unit}"))
        for mapping in run["candidateMappings"]:
            control = control_by_id[mapping["controlAssessmentId"]]
            rows.append((f"Control {control['externalId']}", f"{mapping['state']} · {mapping['relation']} · {mapping['id']}"))
            if mapping["rationale"]:
                rows.append(("Mapping rationale", mapping["rationale"]))
            for review in mapping["reviewHistory"]:
                rows.append(("Review record", ", ".join(f"{key}={value}" for key, value in review.items() if value is not None)))
        sections.append(("Evidence source detail", None, rows))
    return sections


def _sections(report: Dict[str, Any], content_hash: str) -> List[tuple]:
    if report.get("reportType") == SYSTEM_ASSURANCE_REPORT:
        return _system_assurance_sections(report, content_hash)
    return _role_sections(report, content_hash) if _is_role(report) else _snapshot_sections(report, content_hash)


def _bars(report: Dict[str, Any]) -> List[tuple]:
    """(label, [(value, colour, name)]) proportional bars on page one of a role report PDF."""
    m = report.get("data") or {}
    bars = []
    if r := m.get("readiness"):
        bars.append(("Readiness", [(r["met"], "#12805f", "met"), (r["progress"], "#d4930f", "in progress"), (r["attention"], "#c4323a", "need attention"), (r["notstarted"], "#dcdcd6", "not started")]))
    if p := m.get("proof"):
        bars.append(("Proof depth", [(p["measured"], "#2a78d6", "measured"), (p["estimated"], "#86b6ef", "tool estimate"), (p["attested"], "#c7dcf6", "attested"), (p["none"], "#ecebe6", "no proof")]))
    return bars


def _bar_drawing(parts: List[tuple], width: float = 460, height: float = 12):
    from reportlab.graphics.shapes import Drawing, Rect

    drawing = Drawing(width, height)
    total = sum(v for v, _, _ in parts) or 1
    x = 0.0
    for value, colour, _ in parts:
        w = width * value / total
        if w > 0:
            drawing.add(Rect(x, 0, max(w - 1.5, 0.5), height, fillColor=colors.HexColor(colour), strokeColor=None))
        x += w
    return drawing


def generate_snapshot_pdf(report: Dict[str, Any], content_hash: str) -> bytes:
    styles = getSampleStyleSheet()
    title = report.get("title") or "Audit Report"
    is_assurance = report.get("reportType") == SYSTEM_ASSURANCE_REPORT
    story = [Paragraph(escape(title), styles["Title"])]
    if report.get("narrative") and (_is_role(report) or is_assurance):
        story.append(Paragraph(escape(report["narrative"]), styles["BodyText"]))
    if _is_role(report):
        for label, parts in _bars(report):
            story += [Spacer(1, 8), Paragraph(escape(f"{label}: " + ", ".join(f"{v} {n}" for v, _, n in parts)), styles["BodyText"]), _bar_drawing(parts)]
    for heading, head, rows in _sections(report, content_hash):
        story.append(Paragraph(heading, styles["Heading2"]))
        if not rows:
            story.append(Paragraph("None recorded.", styles["Normal"]))
            continue
        cell = lambda v: Paragraph(escape(v), styles["BodyText"])  # noqa: E731
        table = Table([[cell(c) for c in row] for row in ([head] if head else []) + rows], hAlign="LEFT", splitInRow=int(is_assurance))
        table.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.25, colors.grey), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
        story.append(table)
    buffer = BytesIO()
    SimpleDocTemplate(buffer, pagesize=letter, pageCompression=0, title=title).build(story)
    return buffer.getvalue()


def generate_snapshot_docx(report: Dict[str, Any], content_hash: str) -> bytes:
    doc = Document()
    doc.add_heading(report.get("title") or "Audit Report", 0)
    if report.get("narrative") and (_is_role(report) or report.get("reportType") == SYSTEM_ASSURANCE_REPORT):
        doc.add_paragraph(report["narrative"])
    for heading, head, rows in _sections(report, content_hash):
        doc.add_heading(heading, 2)
        if not rows:
            doc.add_paragraph("None recorded.")
            continue
        table = doc.add_table(rows=0, cols=len(rows[0]), style="Table Grid")
        for row in ([head] if head else []) + rows:
            for cell, value in zip(table.add_row().cells, row):
                cell.text = value
    buffer = BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


def generate_snapshot_csv(report: Dict[str, Any], content_hash: str) -> bytes:
    """One CSV for the whole report: a section column, then that section's header and rows (UTF-8 with BOM for spreadsheets)."""
    import csv
    import io

    from src.application.services.clause_map_service import _csv_cell

    buf = io.StringIO()
    writer = csv.writer(buf)
    if report.get("narrative"):
        writer.writerow(["Summary", _csv_cell(report["narrative"])])
    for heading, head, rows in _sections(report, content_hash):
        if head:
            writer.writerow([heading, *head])
        for row in rows:
            writer.writerow([heading, *[_csv_cell(v) for v in row]])
    return buf.getvalue().encode("utf-8-sig")
