import fitz  # PyMuPDF
import docx
import os
from typing import Optional

def extract_text_from_pdf(file_path: str) -> Optional[str]:
    """Extract text from a PDF file.

    Args:
        file_path (str): Path to the PDF file

    Returns:
        Optional[str]: Extracted text or None if extraction fails
    """
    try:
        # Open the PDF file
        with fitz.open(file_path) as pdf_doc:
            # Extract text from all pages
            text = ""
            for page in pdf_doc:
                text += page.get_text()
            return text.strip()
    except Exception as e:
        print(f"Error extracting text from PDF {file_path}: {str(e)}")
        return None

def extract_text_from_docx(file_path: str) -> Optional[str]:
    """Extract text from a DOCX file.

    Args:
        file_path (str): Path to the DOCX file

    Returns:
        Optional[str]: Extracted text or None if extraction fails
    """
    try:
        # Open the DOCX file
        doc = docx.Document(file_path)
        
        # Extract text from all paragraphs
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        
        return text.strip()
    except Exception as e:
        print(f"Error extracting text from DOCX {file_path}: {str(e)}")
        return None

def extract_text(file_path: str) -> Optional[str]:
    """Extract text from PDF or DOCX file.

    Args:
        file_path (str): Path to the file

    Returns:
        Optional[str]: Extracted text or None if extraction fails
    """
    # Get file extension
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    
    if ext == '.pdf':
        return extract_text_from_pdf(file_path)
    elif ext == '.docx':
        return extract_text_from_docx(file_path)
    else:
        print(f"Unsupported file format: {ext}")
        return None