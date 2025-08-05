from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class SessionRequest(BaseModel):
    room_name: str
    judge_id: Optional[str] = None
    human_player_id: Optional[str] = None
    bot_player_id: Optional[str] = None

class SessionResponse(BaseModel):
    id: int
    room_name: str
    judge_id: Optional[str]
    human_player_id: Optional[str]
    bot_player_id: Optional[str]
    status: str
    created_at: datetime
    completed_at: Optional[datetime]

class SessionDetailsResponse(BaseModel):
    session_id: int
    room_name: str
    judge_id: Optional[str]
    human_player_id: Optional[str]
    bot_player_id: Optional[str]
    status: str
    session_created: datetime
    completed_at: Optional[datetime]
    total_questions: int
    total_answers: int
