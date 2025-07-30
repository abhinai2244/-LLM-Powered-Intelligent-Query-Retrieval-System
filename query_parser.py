import concurrent.futures, logging
from utils import call_gemini, call_openai

class QueryParser:
    def __init__(self, gemini_key, openai_key):
        self.gemini_key = gemini_key
        self.openai_key = openai_key

    def parse(self, query: str) -> dict:
        prompt = f"Extract intent/entities from question: '{query}'"
        with concurrent.futures.ThreadPoolExecutor() as ex:
            future = ex.submit(call_gemini, prompt, self.gemini_key)
            try:
                resp = future.result(timeout=5)
                return resp if isinstance(resp, dict) else {}
            except Exception as e:
                logging.warning("Gemini parse timeout/error. Using OpenAI", exc_info=e)
                return call_openai(prompt, self.openai_key)
