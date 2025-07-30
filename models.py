from pydantic import BaseModel
from typing import List

class QueryRequest(BaseModel):
    documents: str  # Comma-separated list of URLs
    questions: List[str]

class QueryResponse(BaseModel):
    answers: List[str]

from pydantic import BaseModel
from typing import List, Optional

class QueryRequest(BaseModel):
    documents: Optional[str] = None  # ✅ Now it's optional
    questions: List[str]
    