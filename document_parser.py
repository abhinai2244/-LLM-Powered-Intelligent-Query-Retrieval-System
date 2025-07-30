import requests
from docx import Document
import os
from urllib.parse import urlparse

try:
    from pdfminer.high_level import extract_text
except ImportError as e:
    raise ImportError("Failed to import pdfminer.high_level. Ensure 'pdfminer.six' is installed. Run 'pip install pdfminer.six==20231228'") from e

class DocumentParser:
    def parse(self, url: str) -> str:
        """Fetch and parse document from URL (PDF/DOCX)."""
        try:
            response = requests.get(url)
            response.raise_for_status()
        except requests.RequestException as e:
            raise ValueError(f"Failed to fetch document from {url}: {str(e)}") from e
        
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        try:
            if filename.lower().endswith(".pdf"):
                temp_file = "temp.pdf"
                with open(temp_file, "wb") as f:
                    f.write(response.content)
                try:
                    text = extract_text(temp_file)
                    os.remove(temp_file)
                except Exception as e:
                    raise ValueError(f"Failed to parse PDF: {str(e)}") from e
            elif filename.lower().endswith(".docx"):
                temp_file = "temp.docx"
                with open(temp_file, "wb") as f:
                    f.write(response.content)
                try:
                    doc = Document(temp_file)
                    text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
                    os.remove(temp_file)
                except Exception as e:
                    raise ValueError(f"Failed to parse DOCX: {str(e)}") from e
            else:
                raise ValueError(f"Unsupported document type for URL: {url} (filename: {filename})")
            return self._clean_text(text)
        except Exception as e:
            raise ValueError(f"Error processing document: {str(e)}") from e

    def parse_local(self, file_path: str) -> str:
        """Parse local PDF file."""
        if not file_path.lower().endswith(".pdf"):
            raise ValueError(f"Unsupported file type: {file_path}")
        try:
            text = extract_text(file_path)
            return self._clean_text(text)
        except Exception as e:
            raise ValueError(f"Failed to parse local PDF {file_path}: {str(e)}") from e

    def _clean_text(self, text: str) -> str:
        """Clean extracted text (remove noise, headers, footers)."""
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return "\n".join(lines)

    def chunk_text(self, text: str, chunk_size: int = 512) -> list:
        """Split text into chunks for embedding."""
        words = text.split()
        return [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]