from io import BytesIO
from PyPDF2 import PdfReader
from docx import Document

def read_pdf(file: BytesIO) -> str:
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

def read_docx(file: BytesIO) -> str:
    document = Document(file)
    text = ""
    for para in document.paragraphs:
        text += para.text + "\n"
    return text

def read_txt(file: BytesIO) -> str:
    return file.read().decode('utf-8')