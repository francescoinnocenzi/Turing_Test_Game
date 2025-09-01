# session_backend.py
from fastapi_sessions.backends.implementations import InMemoryBackend
from uuid import UUID
from schemas.session_data import SessionData

# Istanza unica (singleton) del backend delle sessioni
backend = InMemoryBackend[UUID, SessionData]()

# è un dizionario che mappa: una chiave (UUID) ad un valore SessionData.
# {
#   UUID("123e4567..."): SessionData(session_id=1)
# }