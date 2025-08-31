from pydantic import BaseModel

# 🔹 1. Definisci SessionData
class SessionData(BaseModel):
    user_id: int # id user_logato
    session_id: int | None = None
    room_name: str | None = None