
from pydantic import BaseModel
from uuid import UUID

class SessionInfo(BaseModel):
    id: int
    room_name: str
    created_at: str  # o datetime se vuoi

class AvailableSessionsResponse(BaseModel):
    available_sessions: list[SessionInfo]

class SessionResponse(BaseModel):
    db_session_id: int
    room_name: str
    session_uuid: UUID
    mode: str