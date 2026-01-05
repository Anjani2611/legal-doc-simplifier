from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from io import BytesIO
from datetime import datetime
from pathlib import Path

class PDFGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a5c73'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2a8aa3'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='ClauseText',
            parent=self.styles['BodyText'],
            fontSize=10,
            leftIndent=20,
            spaceAfter=8,
            alignment=TA_JUSTIFY
        ))
    
    def generate(self, filename, simplify_output, timestamp):
        """Generate complete PDF report"""
        buffer = BytesIO()
        
        # Create PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=1*inch,
            bottomMargin=0.75*inch
        )
        
        # Build story
        story = []
        
        # Title page
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph("Legal Document Simplification Report", self.styles['CustomTitle']))
        story.append(Spacer(1, 0.3*inch))
        
        # Metadata
        meta_data = [
            ['Document', Path(filename).name],
            ['Generated', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            ['Upload Time', timestamp if timestamp else 'N/A'],
            ['Report Type', 'Complete Analysis']
        ]
        
        meta_table = Table(meta_data, colWidths=[2*inch, 4*inch])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f4f8')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        story.append(meta_table)
        story.append(PageBreak())
        
        # Executive Summary
        story.append(Paragraph("Executive Summary", self.styles['SectionHeading']))
        summary_text = f"This report provides a comprehensive analysis of {Path(filename).name}. The document has been processed and simplified for clarity and accessibility."
        story.append(Paragraph(summary_text, self.styles['BodyText']))
        story.append(Spacer(1, 0.3*inch))
        
        # Analysis Results
        story.append(Paragraph("Analysis Results", self.styles['SectionHeading']))
        if simplify_output:
            for i, clause in enumerate(simplify_output.get('clauses', []), 1):
                story.append(Paragraph(f"Clause {i}: {clause.get('title', 'Untitled')}", self.styles['Heading3']))
                story.append(Paragraph(f"Original: {clause.get('original_text', 'N/A')}", self.styles['BodyText']))
                story.append(Paragraph(f"Simplified: {clause.get('simplified_text', 'N/A')}", self.styles['ClauseText']))
                story.append(Spacer(1, 0.2*inch))
        
        # Entities
        story.append(PageBreak())
        story.append(Paragraph("Extracted Entities", self.styles['SectionHeading']))
        if simplify_output and simplify_output.get('entities'):
            entity_data = [['Entity Type', 'Value']]
            for entity in simplify_output['entities']:
                entity_data.append([entity.get('type', 'Unknown'), entity.get('value', 'N/A')])
            
            entity_table = Table(entity_data, colWidths=[2*inch, 4*inch])
            entity_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2a8aa3')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')])
            ]))
            story.append(entity_table)
        
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph("Report Generated Successfully", self.styles['BodyText']))
        
        # Build PDF
        doc.build(story)
        
        return buffer.getvalue()
