"""
PDF text extraction module
Extracts embedded text from single-page PDFs.
Note: PDFs already contain text (no OCR needed - text is embedded in the PDF).
"""
import io
import pdfplumber
from typing import Optional


def extract_text_from_pdf(pdf_content: bytes) -> Optional[str]:
    """
    Extract embedded text from PDF file content.
    The PDF already contains text (no OCR processing needed).
    
    Args:
        pdf_content: PDF file content as bytes
        
    Returns:
        Extracted text as string, or None if extraction fails
    """
    try:
        # Convert bytes to BytesIO for pdfplumber
        pdf_file = io.BytesIO(pdf_content)
        
        with pdfplumber.open(pdf_file) as pdf:
            if len(pdf.pages) == 0:
                return None
            
            # Extract text from first (and only) page
            page = pdf.pages[0]
            text = page.extract_text()
            
            return text if text else None
            
    except Exception as e:
        print(f"Error extracting PDF text: {e}")
        return None

