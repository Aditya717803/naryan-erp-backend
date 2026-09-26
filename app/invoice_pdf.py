"""In-memory invoice PDF rendering shared by download endpoints."""

from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer


def render_invoice_pdf(invoice, company_name="Narayan Aluminium") -> bytes:
    """Render the same compact invoice document for either invoice domain."""
    output = BytesIO()
    document = SimpleDocTemplate(
        output, pagesize=A4, rightMargin=12 * mm, leftMargin=12 * mm,
        topMargin=10 * mm, bottomMargin=10 * mm,
    )
    styles = getSampleStyleSheet()
    story = [
        Paragraph(f"<b>{escape(company_name)}</b>", styles["Title"]),
        Paragraph("Tax Invoice", styles["Heading2"]),
        Paragraph(
            f"Invoice No: {escape(str(invoice.invoice_number))} &nbsp;&nbsp; "
            f"Date: {escape(str(invoice.invoice_date))}",
            styles["Normal"],
        ),
        Spacer(1, 5 * mm),
        Paragraph(
            f"Bill To: {escape(str(invoice.customer.name))}",
            styles["Normal"],
        ),
        Spacer(1, 4 * mm),
    ]
    rows = [["#", "Description", "HSN/SAC", "Qty", "Unit", "Rate", "Amount"]]
    for number, item in enumerate(invoice.items, 1):
        rows.append([
            str(number), escape(str(item.description)), escape(str(item.hsn_sac or "")),
            str(item.quantity), escape(str(item.unit)), f"{item.rate:.2f}",
            f"{item.amount:.2f}",
        ])
    rows.append(["", "", "", "", "", "Subtotal", f"{invoice.subtotal:.2f}"])
    rows.append(["", "", "", "", "", "Tax", f"{(invoice.cgst_amount + invoice.sgst_amount + invoice.igst_amount):.2f}"])
    rows.append(["", "", "", "", "", "Grand Total", f"{invoice.grand_total:.2f}"])
    table = Table(rows, repeatRows=1, colWidths=[9 * mm, 65 * mm, 25 * mm, 18 * mm, 18 * mm, 22 * mm, 27 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8eef7")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (3, 1), (-1, -1), "RIGHT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (-2, -3), (-1, -1), "Helvetica-Bold"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.extend([table, Spacer(1, 5 * mm), Paragraph(
        f"Deduct from inventory: {'Yes' if invoice.deduct_from_inventory else 'No'}",
        styles["Normal"],
    )])
    document.build(story)
    return output.getvalue()


def invoices_zip(invoices, filename_prefix):
    import zipfile

    output = BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for invoice in invoices:
            archive.writestr(
                f"{filename_prefix}-{invoice.invoice_number}.pdf",
                render_invoice_pdf(invoice),
            )
    return output.getvalue()
