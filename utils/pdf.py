import io
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

def generate_pdf_invoice(sale, items):
    """
    Generates a clean PDF invoice using ReportLab.
    Returns bytes of the generated PDF or None if ReportLab is unavailable.
    """
    if not HAS_REPORTLAB:
        return None
    sale_data = dict(sale)
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'InvTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=colors.HexColor('#0e0f0c')
    )
    sub_style = ParagraphStyle(
        'InvSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor('#454745'),
        leading=14
    )
    norm = ParagraphStyle(
        'InvNorm',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14
    )

    story = [
        Paragraph('SMARTBIZ ERP', title_style),
        Paragraph('Enterprise Business Management System', sub_style),
        Spacer(1, 15),
        Paragraph(f"<b>Invoice:</b> {sale_data['invoice_no']}", norm),
        Paragraph(f"<b>Date:</b> {sale_data['created_at']}", norm),
        Paragraph(f"<b>Customer:</b> {sale_data['customer'] or 'Walk-in Customer'}", norm),
    ]
    if sale_data.get('phone'):
        story.append(Paragraph(f"<b>Phone:</b> {sale_data['phone']}", norm))
    if sale_data.get('email'):
        story.append(Paragraph(f"<b>Email:</b> {sale_data['email']}", norm))
    story.append(Spacer(1, 15))

    data = [['SKU', 'Product', 'Qty', 'Unit Price', 'Amount']]
    for it in items:
        it_data = dict(it)
        data.append([
            str(it_data['sku']),
            str(it_data['name']),
            str(it_data['qty']),
            f"Rs. {it_data['unit_price']:.2f}",
            f"Rs. {it_data['qty']*it_data['unit_price']:.2f}"
        ])
    data.append(['', '', '', 'Total', f"Rs. {sale_data['total']:.2f}"])

    table = Table(data, colWidths=[70, 200, 45, 90, 90])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0e0f0c')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#9fe870')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('ALIGN', (2,1), (-1,-1), 'RIGHT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTNAME', (-2,-1), (-1,-1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('FONTSIZE', (0,0), (-1,-1), 9)
    ]))

    story.extend([
        table,
        Spacer(1, 15),
        Paragraph(f"<b>Payment:</b> {sale_data['payment_status']} | <b>Method:</b> {sale_data.get('payment_method') or 'UPI'}", norm),
        Spacer(1, 20),
        Paragraph('<i>Thank you for your business.</i>', sub_style)
    ])
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
