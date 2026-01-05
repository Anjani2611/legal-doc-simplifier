from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from io import BytesIO
from datetime import datetime
from pathlib import Path

class SimplePDFGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=20,
            textColor=colors.HexColor('#1a5c73'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=self.styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#2a8aa3'),
            spaceAfter=10,
            spaceBefore=10,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='SimpleText',
            parent=self.styles['BodyText'],
            fontSize=10,
            leftIndent=0,
            spaceAfter=12,
            alignment=TA_JUSTIFY,
            leading=14
        ))
    
    def generate(self, filename, simplify_output, timestamp):
        """Generate simplified text-only PDF"""
        buffer = BytesIO()
        
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=1*inch,
            bottomMargin=0.75*inch
        )
        
        story = []
        
        # Title page
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph("Simplified Document", self.styles['CustomTitle']))
        story.append(Spacer(1, 0.1*inch))
        story.append(Paragraph(f"Source: {Path(filename).name}", self.styles['BodyText']))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M %p')}", self.styles['BodyText']))
        story.append(Spacer(1, 0.3*inch))
        story.append(PageBreak())
        
        # Simplified clauses
        if simplify_output and simplify_output.get('clauses'):
            for i, clause in enumerate(simplify_output['clauses'], 1):
                story.append(Paragraph(f"Section {i} - {clause.get('title', 'Untitled')}", self.styles['SectionHeading']))
                story.append(Paragraph(clause.get('simplified_text', 'No content'), self.styles['SimpleText']))
                story.append(Spacer(1, 0.15*inch))
        
        # Build PDF
        doc.build(story)
        
        return buffer.getvalue()
