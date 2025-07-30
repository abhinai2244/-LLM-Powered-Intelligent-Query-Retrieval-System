import concurrent.futures, logging
from utils import call_gemini, call_openai

class LogicEvaluator:
    def __init__(self, gemini_key=None, openai_key=None):
        self.gemini_key = gemini_key
        self.openai_key = openai_key

    def evaluate(self, question, chunks, timeout=10):
        context = "\n\n".join(chunks)
        prompt = f"Context:\n{context}\n\nQuestion: {question}\n\nAnswer clearly with rationale as JSON."

        def run_gemini():
            return call_gemini(prompt, self.gemini_key)

        def run_openai():
            return call_openai(prompt, self.openai_key)

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
            futures = {
                ex.submit(run_gemini): "Gemini",
                ex.submit(run_openai): "OpenAI"
            }
            done, _ = concurrent.futures.wait(futures, timeout=timeout, return_when=concurrent.futures.FIRST_COMPLETED)
            if not done:
                logging.error("Logic evaluation timed out from both APIs")
                raise RuntimeError("LLM evaluation timeout")

            winner = done.pop()
            try:
                resp = winner.result(timeout=0.1)
                logging.info("%s provided answer", futures[winner])
            except Exception as e:
                logging.error("%s failed evaluation: %s", futures[winner], e)
                raise

        return resp if isinstance(resp, dict) else {"answer": resp}
