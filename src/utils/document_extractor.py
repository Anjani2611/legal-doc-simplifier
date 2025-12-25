"""Extract text from various document formats"""

import logging
from pathlib import Path
from typing import Tuple
import PyPDF2
from docx import Document as DocxDocument

logger = logging.getLogger(__name__)


class DocumentExtractor:
    """Extract text from PDF, DOCX, and TXT files"""
    
    @staticmethod
    def extract_text(file_path: str) -> Tuple[str, str]:
        """
        Extract text from document
        
        Args:
            file_path: Path to file
        
        Returns:
            Tuple of (extracted_text, file_type)
        """
        path = Path(file_path)
        extension = path.suffix.lower()[1:]  # Remove the dot
        
        logger.info(f"Extracting from {path.name} ({extension})")
        
        if extension == "pdf":
            return DocumentExtractor._extract_pdf(file_path), "pdf"
        elif extension == "docx":
            return DocumentExtractor._extract_docx(file_path), "docx"
        elif extension == "txt":
            return DocumentExtractor._extract_txt(file_path), "txt"
        else:
            raise ValueError(f"Unsupported file type: {extension}")
    
    @staticmethod
    def _extract_pdf(file_path: str) -> str:
        """Extract text from PDF"""
        text = []
        try:
            with open(file_path, "rb") as pdf_file:
                reader = PyPDF2.PdfReader(pdf_file)
                for page in reader.pages:
                    text.append(page.extract_text())
            return "\n".join(text)
        except Exception as e:
            logger.error(f"PDF extraction failed: {str(e)}")
            raise
    
    @staticmethod
    def _extract_docx(file_path: str) -> str:
        """Extract text from DOCX"""
        text = []
        try:
            doc = DocxDocument(file_path)
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text.append(paragraph.text)
            return "\n".join(text)
        except Exception as e:
            logger.error(f"DOCX extraction failed: {str(e)}")
            raise
    
    @staticmethod
    def _extract_txt(file_path: str) -> str:
        """Extract text from TXT"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"TXT extraction failed: {str(e)}")
            raise
