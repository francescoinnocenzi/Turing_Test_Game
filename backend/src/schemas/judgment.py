from pydantic import BaseModel
from datetime import datetime

class JudgmentRequest(BaseModel):
    session_id: int
    judge_id: int
    chosen_player_human: str  

class JudgmentResponse(BaseModel):
    id: int
    session_id: int
    judge_id: int
    chosen_player_human: str
    created_at: datetime 
