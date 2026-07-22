"""
Export module — generates PDF and Word documents from HECTOR responses.

Produces court-ready documents with proper formatting, citations,
and metadata. Supports both PDF (via fpdf2) and DOCX (via python-docx).
"""

import io
import logging
import unicodedata
from fpdf.enums import XPos, YPos
from datetime import UTC, datetime

logger = logging.getLogger(__name__)


def _sanitize_for_pdf(text: str) -> str:
    """Replace Unicode characters unsupported by Latin-1 with ASCII equivalents."""
    replacements = {
        "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
        "\u2014": " - ", "\u2013": "-", "\u2026": "...",
        "\u00a0": " ", "\u2022": "*", "\u00b6": "",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return unicodedata.normalize("NFKD", text).encode("latin-1", "replace").decode("latin-1")


def export_pdf(response_data: dict) -> bytes:
    """
    Generate a PDF document from a HECTOR search response.

    Args:
        response_data: dict with keys: query, generated_response, answer_sections,
                       source_sections, citations, route, confidence, etc.

    Returns:
        PDF file bytes.
    """
    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # --- Title ---
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "HECTOR Legal Research Report", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")

    # --- Metadata ---
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(120, 120, 120)
    generated_at = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    pdf.cell(0, 6, f"Generated: {generated_at}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.ln(4)

    # --- Divider ---
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(6)

    # --- Query ---
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "Query", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 10)
    query = response_data.get("query", "N/A")
    pdf.multi_cell(0, 6, _sanitize_for_pdf(query))
    pdf.ln(3)

    # --- Route & Confidence ---
    route = response_data.get("route", "LEGAL_RESEARCH")
    confidence = response_data.get("answer_confidence", 0)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, f"Route: {route}  |  Confidence: {confidence}%", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)

    # --- Divider ---
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(6)

    # --- Generated Response ---
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "Response", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 10)
    response_text = response_data.get("generated_response", "No response generated.")
    for paragraph in response_text.split("\n\n"):
        paragraph = paragraph.strip()
        if paragraph:
            pdf.multi_cell(0, 6, _sanitize_for_pdf(paragraph))
            pdf.ln(2)

    # --- Answer Sections ---
    answer_sections = response_data.get("answer_sections", [])
    if answer_sections:
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 7, "Answer Sections", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("Helvetica", "", 10)
        for i, section in enumerate(answer_sections, 1):
            title = section.get("title", f"Section {i}")
            body = section.get("body", "")
            pdf.set_font("Helvetica", "B", 10)
            pdf.multi_cell(0, 6, _sanitize_for_pdf(f"{i}. {title}"))
            pdf.set_font("Helvetica", "", 10)
            if body:
                pdf.multi_cell(0, 6, _sanitize_for_pdf(body))
            pdf.ln(2)

    # --- Citations ---
    citations = response_data.get("citations", [])
    if citations:
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 7, "Citations", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("Helvetica", "", 9)
        for i, citation in enumerate(citations, 1):
            if isinstance(citation, dict):
                act = citation.get("act", "")
                section = citation.get("section", "")
                text = citation.get("text", "")
                cite_str = f"{i}. {act} Section {section}"
                if text:
                    cite_str += f" — {text[:120]}"
            else:
                cite_str = f"{i}. {str(citation)}"
            pdf.multi_cell(0, 5, _sanitize_for_pdf(cite_str))
            pdf.ln(1)

    # --- Source Sections ---
    source_sections = response_data.get("source_sections", [])
    if source_sections:
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 7, "Source Sections", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("Helvetica", "", 9)
        for i, src in enumerate(source_sections, 1):
            act = src.get("act", "")
            section = src.get("section", "")
            pdf.multi_cell(0, 5, f"{i}. {act} Section {section}")
            pdf.ln(1)

    # --- Footer ---
    pdf.ln(10)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(150, 150, 150)
    pdf.multi_cell(
        0,
        4,
        "This document was generated by HECTOR (Hierarchical Evaluation of "
        "Civil-Criminal Textual's Orchestrator & Retrieval). Responses are "
        "AI-generated and should be verified against official legal texts. "
        "This is not legal advice.",
        align="C",
    )

    # Output bytes
    output = io.BytesIO()
    pdf_data = pdf.output()
    if isinstance(pdf_data, str):
        pdf_data = pdf_data.encode("latin-1")
    output.write(pdf_data)
    return output.getvalue()


def export_docx(response_data: dict) -> bytes:
    """
    Generate a Word document from a HECTOR search response.

    Args:
        response_data: dict with keys: query, generated_response, answer_sections,
                       source_sections, citations, route, confidence, etc.

    Returns:
        DOCX file bytes.
    """
    from docx import Document
    from docx.shared import Pt, Inches, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    doc = Document()

    # --- Style defaults ---
    style = doc.styles["Normal"]
    font = style.font
    font.name = "Calibri"
    font.size = Pt(10)

    # --- Title ---
    title = doc.add_heading("HECTOR Legal Research Report", level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # --- Metadata ---
    meta = doc.add_paragraph()
    meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = meta.add_run(f"Generated: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}")
    run.font.size = Pt(9)
    run.font.color.rgb = RGBColor(120, 120, 120)

    doc.add_paragraph()  # spacer

    # --- Query ---
    doc.add_heading("Query", level=1)
    doc.add_paragraph(response_data.get("query", "N/A"))

    # --- Route & Confidence ---
    route = response_data.get("route", "LEGAL_RESEARCH")
    confidence = response_data.get("answer_confidence", 0)
    meta_p = doc.add_paragraph()
    run = meta_p.add_run(f"Route: {route}  |  Confidence: {confidence}%")
    run.font.size = Pt(9)
    run.font.color.rgb = RGBColor(100, 100, 100)

    doc.add_paragraph()  # spacer

    # --- Generated Response ---
    doc.add_heading("Response", level=1)
    response_text = response_data.get("generated_response", "No response generated.")
    for paragraph in response_text.split("\n\n"):
        paragraph = paragraph.strip()
        if paragraph:
            doc.add_paragraph(paragraph)

    # --- Answer Sections ---
    answer_sections = response_data.get("answer_sections", [])
    if answer_sections:
        doc.add_heading("Answer Sections", level=1)
        for i, section in enumerate(answer_sections, 1):
            title = section.get("title", f"Section {i}")
            body = section.get("body", "")
            doc.add_heading(f"{i}. {title}", level=2)
            if body:
                doc.add_paragraph(body)

    # --- Citations ---
    citations = response_data.get("citations", [])
    if citations:
        doc.add_page_break()
        doc.add_heading("Citations", level=1)
        for i, citation in enumerate(citations, 1):
            if isinstance(citation, dict):
                act = citation.get("act", "")
                section_num = citation.get("section", "")
                text = citation.get("text", "")
                cite_str = f"{act} Section {section_num}"
                if text:
                    cite_str += f" — {text[:200]}"
            else:
                cite_str = str(citation)
            p = doc.add_paragraph()
            run = p.add_run(f"{i}. ")
            run.bold = True
            p.add_run(cite_str)

    # --- Source Sections ---
    source_sections = response_data.get("source_sections", [])
    if source_sections:
        doc.add_heading("Source Sections", level=1)
        for i, src in enumerate(source_sections, 1):
            act = src.get("act", "")
            section_num = src.get("section", "")
            doc.add_paragraph(f"{i}. {act} Section {section_num}")

    # --- Footer ---
    doc.add_paragraph()
    footer = doc.add_paragraph()
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = footer.add_run(
        "This document was generated by HECTOR (Hierarchical Evaluation of "
        "Civil-Criminal Textual's Orchestrator & Retrieval). Responses are "
        "AI-generated and should be verified against official legal texts. "
        "This is not legal advice."
    )
    run.font.size = Pt(8)
    run.font.italic = True
    run.font.color.rgb = RGBColor(150, 150, 150)

    # Output bytes
    output = io.BytesIO()
    doc.save(output)
    return output.getvalue()
