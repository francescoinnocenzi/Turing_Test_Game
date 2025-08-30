# session_backend.py
from fastapi_sessions.backends.implementations import InMemoryBackend
from uuid import UUID
from schemas.session_data import SessionData

# Istanza unica (singleton) del backend delle sessioni
backend = InMemoryBackend[UUID, SessionData]()
