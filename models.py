from pydantic import BaseModel
from typing import List, Union

class RunRequest(BaseModel):
    documents: Union[str, List[str]]  # Accept a string or list of URLs
    questions: List[str]

class RunResponse(BaseModel):
    answers: List[str]
