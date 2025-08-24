from pydantic import BaseModel

class ResponseAPI(BaseModel):
    answer: str
    chat_history: list[dict]

class RequestAPI(BaseModel):
    question: str