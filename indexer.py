import pdfplumber
from langchain_community.document_loaders import UnstructuredWordDocumentLoader
from langchain_core.documents import Document
try:
    import pytesseract
    from pdf2image import convert_from_path
    OCR_ENABLED = True
except ImportError:
    OCR_ENABLED = False
import os
import time

def load_and_index(file_path):
    start_time = time.time()
    text = ""
    if file_path.endswith(".pdf"):
        try:
            with pdfplumber.open(file_path) as pdf:
                total_pages = len(pdf.pages)
                for i, page in enumerate(pdf.pages):
                    # Extract text with layout preservation
                    try:
                        page_text = page.extract_text(layout=True, x_tolerance=5, y_tolerance=5)
                        if page_text and isinstance(page_text, str):
                            text += f"\n--- Page {i+1} ---\n{page_text}\n"
                        else:
                            text += f"\n--- Page {i+1} (No Text Extracted) ---\n"
                    except Exception as e:
                        print(f"Text extraction failed for page {i+1}: {str(e)}")
                        text += f"\n--- Page {i+1} (Text Extraction Failed) ---\n"
                    # Extract tables with simpler settings
                    try:
                        tables = page.extract_tables({
                            "vertical_strategy": "lines",
                            "horizontal_strategy": "lines",
                            "snap_tolerance": 6,
                            "min_words_vertical": 1,
                            "min_words_horizontal": 1
                        })
                        if tables:
                            for table in tables:
                                table_text = "\n".join([" ".join(str(cell or "") for cell in row) for row in table if row])
                                text += f"\n--- Table from Page {i+1} ---\n{table_text}\n"
                        else:
                            text += f"\n--- Table from Page {i+1} (No Tables Detected) ---\n"
                    except Exception as e:
                        print(f"Table extraction failed for page {i+1}: {str(e)}")
                    # Apply OCR for pages with minimal or no text
                    if (not page_text or (isinstance(page_text, str) and len(page_text.strip()) < 500)) and OCR_ENABLED:
                        try:
                            images = convert_from_path(file_path, first_page=i+1, last_page=i+1, dpi=400, fmt="png")
                            for image in images:
                                ocr_text = pytesseract.image_to_string(image, config='--psm 6 --oem 3 -l eng')
                                if ocr_text.strip():
                                    text += f"\n--- OCR Page {i+1} ---\n{ocr_text}\n"
                                else:
                                    text += f"\n--- OCR Page {i+1} (No Text Detected) ---\n"
                        except Exception as e:
                            print(f"OCR failed for page {i+1}: {str(e)}")
            # Log extracted text
            safe_filename = os.path.basename(file_path).replace(":", "_").replace("/", "_").replace("\\", "_")
            log_path = os.path.join(os.path.dirname(file_path), f"extracted_text_{safe_filename}.txt")
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(text)
        except Exception as e:
            raise ValueError(f"Failed to extract text from PDF: {str(e)}")
    elif file_path.endswith(".docx"):
        loader = UnstructuredWordDocumentLoader(file_path)
        docs = loader.load()
        text = "\n".join([doc.page_content for doc in docs])
    else:
        raise ValueError("Unsupported file type")
    
    print(f"Text extraction took: {time.time() - start_time:.2f} seconds")
    print(f"Extracted characters: {len(text)}")
    print(f"Total pages processed: {total_pages}")
    return [Document(page_content=text)]