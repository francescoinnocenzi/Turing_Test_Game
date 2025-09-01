from pydantic import BaseModel
from typing import Optional

class ResponseAPI(BaseModel):
    answer: str
    chat_history: list[dict]

class RequestAPI(BaseModel):
    question: str

class SimilarityResponse(BaseModel):
    frase_input: str
    frase_simile: Optional[str] = None  # ora può essere None
    risposta_trovata: str
    similarita: float
    tipo_risposta: str