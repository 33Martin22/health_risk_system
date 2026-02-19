"""
reports.py - PDF report generation
Generates downloadable medical assessment reports
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
from datetime import datetime


RISK_COLORS_RGB = {
    'Low':    colors.HexColor('#2ecc71'),
    'Medium': colors.HexColor('#f39c12'),
    'High':   colors.HexColor('#e74c3c'),
}

PRIMARY_COLOR = colors.HexColor('#1a4a7a')
LIGHT_BG = colors.HexColor('#f0f4f8')


def generate_pdf_report(patient_info: dict, vitals: dict, risk_level: str,
                         risk_score: float, probabilities: dict,
                         recommendations: list, abnormal_vitals: dict) -> bytes:
    """
    Generate a professional PDF medical report.
    Returns bytes object of the PDF.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle', parent=styles['Title'],
        fontSize=22, textColor=PRIMARY_COLOR,
        spaceAfter=4, fontName='Helvetica-Bold', alignment=TA_CENTER
    )
    subtitle_style = ParagraphStyle(
        'Subtitle', parent=styles['Normal'],
        fontSize=10, textColor=colors.HexColor('#64748b'),
        spaceAfter=2, alignment=TA_CENTER
    )
    section_header_style = ParagraphStyle(
        'SectionHeader', parent=styles['Heading2'],
        fontSize=13, textColor=PRIMARY_COLOR,
        spaceBefore=14, spaceAfter=6, fontName='Helvetica-Bold',
        borderPad=4
    )
    body_style = ParagraphStyle(
        'Body', parent=styles['Normal'],
        fontSize=10, spaceAfter=4, leading=16
    )
    rec_style = ParagraphStyle(
        'Recommendation', parent=styles['Normal'],
        fontSize=10, spaceAfter=4, leading=16, leftIndent=10
    )

    content = []

    # ── HEADER ──────────────────────────────────────────────
    content.append(Paragraph("🏥 AI-Powered Health Risk Assessment", title_style))
    content.append(Paragraph("Medical Assessment Report", subtitle_style))
    content.append(Paragraph(
        f"Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
        subtitle_style
    ))
    content.append(HRFlowable(width="100%", thickness=2, color=PRIMARY_COLOR, spaceAfter=12))

    # ── PATIENT INFORMATION ──────────────────────────────────
    content.append(Paragraph("Patient Information", section_header_style))

    patient_data = [
        ['Full Name', patient_info.get('full_name', 'N/A'),
         'Patient ID', f"#{patient_info.get('id', 'N/A')}"],
        ['Username', patient_info.get('username', 'N/A'),
         'Email', patient_info.get('email', 'N/A')],
        ['Assessment Date', datetime.now().strftime('%B %d, %Y'),
         'Assessment Time', datetime.now().strftime('%I:%M %p')],
    ]

    patient_table = Table(patient_data, colWidths=[3.5*cm, 6*cm, 3.5*cm, 6*cm])
    patient_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), LIGHT_BG),
        ('BACKGROUND', (2, 0), (2, -1), LIGHT_BG),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (0, -1), PRIMARY_COLOR),
        ('TEXTCOLOR', (2, 0), (2, -1), PRIMARY_COLOR),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, LIGHT_BG]),
    ]))
    content.append(patient_table)
    content.append(Spacer(1, 12))

    # ── RISK CLASSIFICATION ──────────────────────────────────
    content.append(Paragraph("Risk Classification Result", section_header_style))

    risk_color = RISK_COLORS_RGB.get(risk_level, colors.gray)
    risk_data = [
        ['Risk Level', risk_level, 'Confidence Score', f"{risk_score:.1f}%"],
        ['Low Risk', f"{probabilities.get('Low', 0):.1f}%",
         'Medium Risk', f"{probabilities.get('Medium', 0):.1f}%"],
        ['High Risk', f"{probabilities.get('High', 0):.1f}%", '', ''],
    ]

    risk_table = Table(risk_data, colWidths=[3.5*cm, 6*cm, 3.5*cm, 6*cm])
    risk_table.setStyle(TableStyle([
        ('BACKGROUND', (1, 0), (1, 0), risk_color),
        ('TEXTCOLOR', (1, 0), (1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONTSIZE', (1, 0), (1, 0), 13),
        ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 0), (0, -1), PRIMARY_COLOR),
        ('TEXTCOLOR', (2, 0), (2, -1), PRIMARY_COLOR),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('ALIGN', (1, 0), (1, 0), TA_CENTER),
    ]))
    content.append(risk_table)
    content.append(Spacer(1, 12))

    # ── VITAL SIGNS ──────────────────────────────────────────
    content.append(Paragraph("Vital Signs", section_header_style))

    vital_headers = [['Vital Sign', 'Value', 'Normal Range', 'Status']]
    vital_rows = [
        ['Respiratory Rate', f"{vitals.get('respiratory_rate', 'N/A')} breaths/min", '12 - 20', ''],
        ['Oxygen Saturation (SpO2)', f"{vitals.get('oxygen_saturation', 'N/A')}%", '95 - 100%', ''],
        ['Systolic Blood Pressure', f"{vitals.get('systolic_bp', 'N/A')} mmHg", '90 - 140', ''],
        ['Heart Rate', f"{vitals.get('heart_rate', 'N/A')} bpm", '60 - 100', ''],
        ['Body Temperature', f"{vitals.get('temperature', 'N/A')} °C", '36.1 - 37.5', ''],
        ['O2 Scale', f"{vitals.get('o2_scale', 'N/A')}", '0 - 2', ''],
        ['Consciousness', vitals.get('consciousness', 'N/A'), 'Alert (A)', ''],
        ['On Oxygen', 'Yes' if vitals.get('on_oxygen') == 1 else 'No', 'No', ''],
    ]

    normal_ranges = {
        'respiratory_rate': (12, 20),
        'oxygen_saturation': (95, 100),
        'systolic_bp': (90, 140),
        'heart_rate': (60, 100),
        'temperature': (36.1, 37.5),
    }
    vital_keys = ['respiratory_rate', 'oxygen_saturation', 'systolic_bp',
                  'heart_rate', 'temperature']

    for i, key in enumerate(vital_keys):
        val = vitals.get(key)
        lo, hi = normal_ranges[key]
        if val is not None:
            if val < lo:
                vital_rows[i][3] = '⚠ LOW'
            elif val > hi:
                vital_rows[i][3] = '⚠ HIGH'
            else:
                vital_rows[i][3] = '✓ Normal'

    vital_table = Table(vital_headers + vital_rows,
                        colWidths=[5.5*cm, 4.5*cm, 4*cm, 3*cm])
    vital_style = [
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('PADDING', (0, 0), (-1, -1), 7),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ('ALIGN', (1, 0), (-1, -1), TA_CENTER),
    ]
    # Highlight abnormal rows
    for i, key in enumerate(vital_keys):
        if key in abnormal_vitals:
            vital_style.append(('TEXTCOLOR', (3, i+1), (3, i+1), colors.HexColor('#e74c3c')))
            vital_style.append(('FONTNAME', (3, i+1), (3, i+1), 'Helvetica-Bold'))

    vital_table.setStyle(TableStyle(vital_style))
    content.append(vital_table)
    content.append(Spacer(1, 12))

    # ── RECOMMENDATIONS ──────────────────────────────────────
    content.append(Paragraph("Medical Recommendations", section_header_style))
    for rec in recommendations:
        clean_rec = rec.replace('✅', '•').replace('⚠️', '•').replace('🚨', '!!').replace('🏥', '')
        clean_rec = clean_rec.replace('👨‍⚕️', '').replace('📊', '').replace('💊', '').replace('🧘', '')
        clean_rec = clean_rec.replace('🍎', '').replace('📞', '').replace('🚫', '').replace('👥', '')
        clean_rec = clean_rec.replace('📱', '').replace('📋', '').replace('🥗', '').replace('💧', '')
        clean_rec = clean_rec.replace('🏃', '').replace('📅', '').replace('🚭', '')
        content.append(Paragraph(clean_rec.strip(), rec_style))

    content.append(Spacer(1, 16))

    # ── DISCLAIMER ───────────────────────────────────────────
    content.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e2e8f0')))
    content.append(Spacer(1, 8))
    disclaimer_style = ParagraphStyle(
        'Disclaimer', parent=styles['Normal'],
        fontSize=8, textColor=colors.HexColor('#94a3b8'),
        alignment=TA_CENTER, leading=12
    )
    content.append(Paragraph(
        "This report is generated by an AI-powered system and is intended for informational purposes only. "
        "It does not constitute medical advice. Always consult a qualified healthcare professional for diagnosis and treatment.",
        disclaimer_style
    ))

    doc.build(content)
    return buffer.getvalue()
