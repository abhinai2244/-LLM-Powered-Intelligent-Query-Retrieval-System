import os
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyBhp3aZU4yw6psLVYqneG2ZNbtoAV2lcmI")
VECTOR_INDEX_PATH = "faiss_index"
SQLITE_PATH = "klbase.sqlite"
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text:latest")