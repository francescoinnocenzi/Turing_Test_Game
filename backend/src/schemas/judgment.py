from pydantic import BaseModel
from datetime import datetime
from typing import Optional

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

class LLMJudgmentResponse(BaseModel):
    # correct_answer: bool
    # llm_choice: Optional[str]
    judgment: str
    # session_id: int
    # human_responses: int
    # bot_responses: int
    # correct_guess: str
    human_result: str
