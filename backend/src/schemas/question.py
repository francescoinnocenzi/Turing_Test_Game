from pydantic import BaseModel
from datetime import datetime

class QuestionRequest(BaseModel):
    session_id: int
    text: str
    author_id: str
    room_name: str

class QuestionResponse(BaseModel):
    id: int
    text: str
    session_id: int
    author_id: str
    room_name: str
    created_at: datetime
