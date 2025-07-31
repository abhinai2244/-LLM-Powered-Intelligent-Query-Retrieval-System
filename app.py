from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import Union, List
import requests
import tempfile
import os
from urllib.parse import urlparse
from querier import process_query
from indexer import load_and_index
from langchain_core.documents import Document
from google.api_core.exceptions import ResourceExhausted
import time

app = FastAPI()

# Define OAuth2 scheme for bearer token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Hardcoded bearer token from documentation
VALID_BEARER_TOKEN = "30450808dab37b3b611d0ba9cc36afefc500b2d28fd961e682435572d7aa6caa"

# Dependency to validate bearer token
async def verify_token(token: str = Depends(oauth2_scheme)):
    if token != VALID_BEARER_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token

class QueryRequest(BaseModel):
    documents: Union[str, List[str]]  # Accept string or list of URLs
    questions: List[str]

def download_file(url: str) -> str:
    parsed_url = urlparse(url)
    clean_path = parsed_url.path
    suffix = os.path.splitext(clean_path)[1].lower()
    
    response = requests.get(url)
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail=f"Failed to download document: {url}")
    
    if suffix not in ['.pdf', '.docx']:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {suffix}")
    
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp_file.write(response.content)
    tmp_file.close()
    return tmp_file.name

@app.post("/api/v1/hackrx/run")
async def run_query(request: QueryRequest, token: str = Depends(verify_token)):
    if len(request.questions) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 questions allowed")
    
    # Convert single document string to list for consistent processing
    document_urls = [request.documents] if isinstance(request.documents, str) else request.documents
    
    answers = []
    file_paths = []
    text_cache = {}  # Cache extracted text per document
    try:
        # Download and extract text for each document once
        for url in document_urls:
            file_path = download_file(url)
            file_paths.append((url, file_path))
            # Extract text once using load_and_index
            try:
                docs = load_and_index(file_path)
                text_cache[url] = "\n".join([doc.page_content for doc in docs])
            except Exception as e:
                text_cache[url] = None
                print(f"Failed to extract text for {url}: {str(e)}")
        
        for question in request.questions:
            time.sleep(6)  # Respect 10 RPM for Gemini 2.5 Flash
            for url, file_path in file_paths:
                try:
                    # Use cached text if available
                    if text_cache.get(url):
                        from querier import process_query_with_text
                        result = process_query_with_text(text_cache[url], question)
                        answer = result["llm_response"]["raw_answer"]
                    else:
                        # Fallback to original process_query if text extraction failed
                        result = process_query(file_path, question)
                        answer = result["llm_response"]["raw_answer"]
                    
                    # Format answer to match required style
                    if answer.startswith("Answer:"):
                        answer = answer.replace("Answer:", "").strip()
                    if "Answer not found" in answer:
                        answer = "Answer not found. The document may not contain the relevant information."
                    answers.append(answer)
                except ResourceExhausted as e:
                    answers.append(f"Error: Gemini API quota exceeded: {str(e)}. Please wait and try again or check your plan at https://ai.google.dev/gemini-api/docs/rate-limits.")
                except Exception as e:
                    answers.append(f"Error: Internal server error: {str(e)}")
    finally:
        for _, file_path in file_paths:
            if os.path.exists(file_path):
                os.remove(file_path)
    return {"answers": answers}