from pydantic import BaseModel
from datetime import datetime

class QuestionRequest(BaseModel):
    session_id: int
    text: str
    author_user_id: int | None
    author_type: str
    room_name: str

class QuestionResponse(BaseModel):
    id: int
    text: str
    session_id: int
    author_user_id: int | None
    room_name: str
    created_at: datetime
