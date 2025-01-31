from io import BytesIO
from PyPDF2 import PdfReader
from docx import Document

class FileHandler:
    def extract_text(self, content: bytes, content_type: str) -> str:
        content_io = BytesIO(content)
        
        if content_type == "application/pdf":
            return self._read_pdf(content_io)
        elif content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return self._read_docx(content_io)
        elif content_type == "text/plain":
            return self._read_txt(content_io)
        else:
            raise ValueError(f"Unsupported file type: {content_type}")

    def _read_pdf(self, file: BytesIO) -> str:
        # Existing PDF reading logic
        pass

    def _read_docx(self, file: BytesIO) -> str:
        # Existing DOCX reading logic
        pass

    def _read_txt(self, file: BytesIO) -> str:
        # Existing TXT reading logic
        pass 