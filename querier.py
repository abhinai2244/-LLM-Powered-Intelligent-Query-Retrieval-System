import google.generativeai as genai
import config
from indexer import load_and_index
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from google.api_core.exceptions import ResourceExhausted
import time
import re

query_cache = {}
DAILY_TOKEN_LIMIT = 100000000000000000  # Gemini 2.5 Flash free tier
REQUESTS_PER_MINUTE = 10

def clean_response(text):
    """Remove escape characters and normalize text."""
    text = re.sub(r'\\+["\\]', '', text)
    text = re.sub(r'\s+', ' ', text.strip())
    text = text.replace(' .', '.').replace(' ,', ',')
    return text

def process_query(file_path, question: str):
    start_time = time.time()
    cache_key = f"{file_path}:{question}"
    query_cache.clear()
    print(f"Cache cleared for fresh extraction")

    docs = load_and_index(file_path)
    full_text = "\n".join([doc.page_content for doc in docs])
    print(f"Text extraction took: {time.time() - start_time:.2f} seconds")

    return process_query_with_text(full_text, question)

def process_query_with_text(full_text: str, question: str):
    start_time = time.time()
    cache_key = f"text:{question}"
    
    # Filter relevant text
    max_text_size = 120000000  # ~3000 tokens
    relevant_text = full_text[:max_text_size]
    keywords = r"(grace period|pre-existing disease|maternity|cataract|organ donor|no claim discount|health check-up|hospital|ayush|room rent|icu)"
    matches = list(re.finditer(f"{keywords}[^\n]*(\n[^\n]*){0,40}", full_text.lower(), re.IGNORECASE))
    for match in sorted(matches, key=lambda x: x.start()):
        relevant_text += full_text[match.start():match.end()] + "\n"
        if len(relevant_text) >= max_text_size:
            break
    if not relevant_text:
        relevant_text = full_text[:max_text_size]
    
    genai.configure(api_key=config.GOOGLE_API_KEY)
    model = genai.GenerativeModel("gemini-2.5-flash")

    prompt = f"""You are an expert at analyzing insurance policy documents. Read the provided document text and extract the answer to the question. Focus on coverage details, numerical values (e.g., ₹ amounts, time periods), and specific terms or requirements in the benefits, coverage, or definitions sections. Provide a concise plain text answer with full stops for punctuation. Avoid special characters like quotes or backslashes. If the answer is not found, state: Answer not found. The document may not contain the relevant information. Include a brief explanation for missing answers.

Question: {question}

Document text:
{relevant_text}

Answer:"""

    print("\n======= PROMPT TO GEMINI =======\n")
    print(prompt)
    print("\n===============================\n")

    token_count = len(prompt) // 4
    if token_count > DAILY_TOKEN_LIMIT:
        raise Exception(f"Token limit exceeded: {token_count}/{DAILY_TOKEN_LIMIT}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=10, max=60),
        retry=retry_if_exception_type(ResourceExhausted),
        reraise=True
    )
    def call_gemini():
        api_start = time.time()
        response = model.generate_content(prompt)
        print(f"Gemini API call took: {time.time() - api_start:.2f} seconds")
        return clean_response(response.text)

    try:
        answer = call_gemini()
    except ResourceExhausted as e:
        return {
            "query": question,
            "llm_response": {
                "raw_answer": f"Error: Gemini API quota exceeded: {str(e)}. Please wait and try again or check your plan at https://ai.google.dev/gemini-api/docs/rate-limits."
            }
        }

    result = {
        "query": question,
        "llm_response": {
            "raw_answer": answer
        }
    }
    query_cache[cache_key] = result
    print(f"Total processing time: {time.time() - start_time:.2f} seconds")
    print(f"Tokens used: {token_count}/{DAILY_TOKEN_LIMIT}")
    return result