import concurrent.futures, logging
from utils import call_gemini, call_openai

class ClauseMatcher:
    def __init__(self, gemini_key=None, openai_key=None):
        self.gemini_key = gemini_key
        self.openai_key = openai_key

    def match(self, question, chunks):
        relevant = []
        for ch in chunks:
            prompt = f"Is this relevant to the question?\nQuestion: {question}\nChunk:\n{ch}"

            def run_gemini():
                return call_gemini(prompt, self.gemini_key)

            def run_openai():
                return call_openai(prompt, self.openai_key)

            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
                futures = {
                    ex.submit(run_gemini): "Gemini",
                    ex.submit(run_openai): "OpenAI"
                }
                done, _ = concurrent.futures.wait(futures, timeout=6, return_when=concurrent.futures.FIRST_COMPLETED)
                if not done:
                    logging.warning("Clause match timed out for both APIs")
                    continue

                winner = done.pop()
                source = futures[winner]
                try:
                    resp = winner.result(timeout=0.1)
                    logging.info("%s responded for clause match", source)
                except Exception as e:
                    logging.warning("%s failed on clause match: %s", source, e)
                    continue

            if isinstance(resp, dict) and resp.get("relevant"):
                relevant.append(ch)
        return relevant
