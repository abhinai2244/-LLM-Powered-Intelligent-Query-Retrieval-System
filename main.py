import concurrent.futures
import logging
import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uuid
from document_parser import DocumentParser
from embedding_search import EmbeddingSearch
from clause_matcher import ClauseMatcher
from logic_evaluator import LogicEvaluator
from query_parser import QueryParser
from utils import call_gemini, call_openai

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "fallback_gemini_key")
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "fallback_openai_key")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "fallback_pinecone_key")
PINECONE_ENV = os.getenv("PINECONE_ENV", "us-west1-gcp")

# Initialize components
app = FastAPI()
parser = DocumentParser()
embedder = EmbeddingSearch(pinecone_api_key=PINECONE_API_KEY, pinecone_env=PINECONE_ENV)
matcher = ClauseMatcher(gemini_key=GEMINI_KEY, openai_key=OPENAI_KEY)
evaluator = LogicEvaluator(gemini_key=GEMINI_KEY, openai_key=OPENAI_KEY)
query_parser = QueryParser(gemini_key=GEMINI_KEY, openai_key=OPENAI_KEY)

class QueryRequest(BaseModel):
    documents: Optional[str] = None
    questions: List[str]

class QueryResponse(BaseModel):
    answers: List[dict]

@app.post("/hackrx/run", response_model=QueryResponse)
async def run_query(request: QueryRequest):
    try:
        # Step 1: Parse document(s)
        if not request.documents:
            raise HTTPException(status_code=400, detail="No document URLs provided")
        
        doc_urls = [url.strip() for url in request.documents.split(",")]
        all_chunks = []
        doc_id = str(uuid.uuid4())  # Unique ID for this document set
        
        for url in doc_urls:
            logger.info("Parsing document: %s", url)
            text = parser.parse(url)
            chunks = parser.chunk_text(text, chunk_size=512)
            all_chunks.extend(chunks)
            
            # Store embeddings
            embedder.store_embeddings(chunks, doc_id)

        # Step 2: Process each question
        answers = []
        for question in request.questions:
            logger.info("Processing question: %s", question)

            # Parse query intent
            parsed_query = query_parser.parse(question)
            logger.info("Parsed query intent: %s", parsed_query)

            # Step 3: Embedding search
            search_results = embedder.search(question, top_k=5)
            relevant_chunk_ids = [result["id"] for result in search_results]
            relevant_chunks = [
                chunk for i, chunk in enumerate(all_chunks)
                if f"{doc_id}_{i}" in relevant_chunk_ids
            ]

            # Step 4: Clause matching
            matched_chunks = matcher.match(question, relevant_chunks)
            if not matched_chunks:
                logger.warning("No relevant chunks matched for question: %s", question)
                answers.append({
                    "question": question,
                    "answer": "No relevant information found",
                    "rationale": "No clauses matched the query after semantic search and clause matching."
                })
                continue

            # Step 5: Logic evaluation
            try:
                evaluation = evaluator.evaluate(question, matched_chunks, timeout=10)
                answers.append({
                    "question": question,
                    "answer": evaluation.get("answer", "No answer provided"),
                    "rationale": evaluation.get("rationale", "Rationale not provided by LLM"),
                    "matched_chunks": matched_chunks
                })
            except Exception as e:
                logger.error("Evaluation failed for question %s: %s", question, str(e))
                answers.append({
                    "question": question,
                    "answer": "Error processing question",
                    "rationale": f"Evaluation failed: {str(e)}",
                    "matched_chunks": matched_chunks
                })

        return QueryResponse(answers=answers)

    except Exception as e:
        logger.error("Processing failed: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)