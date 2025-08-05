from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AnswerRequest(BaseModel):
    question_id: int
    session_id: int
    text: str
    author_id: str
    author_type: str  # 'HUMAN' or 'BOT'
    room_name: str

class AnswerResponse(BaseModel):
    id: int
    question_id: int
    session_id: int
    text: str
    author_id: str
    author_type: str
    room_name: str
    created_at: datetime
