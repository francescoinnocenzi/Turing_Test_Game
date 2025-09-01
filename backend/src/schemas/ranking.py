
from pydantic import BaseModel

class RankingEntry(BaseModel):
    username: str
    total_score: int

class RankingResponse(BaseModel):
    ranking: list[RankingEntry]