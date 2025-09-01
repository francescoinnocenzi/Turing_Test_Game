from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import List


class SessionInfo(BaseModel):
    """
    Modello che rappresenta le informazioni di una sessione.

    Attributes
        id (int): Identificativo univoco della sessione nel database.
        room_name (str): Nome della stanza associata alla sessione.
        created_at (datetime): Timestamp di creazione della sessione.
    """
    id: int
    room_name: str
    created_at: datetime


class AvailableSessionsResponse(BaseModel):
    """
    Modello di risposta per la lista delle sessioni disponibili.

    Attributes
        available_sessions (List[SessionInfo]): Elenco delle sessioni attive disponibili.
    """
    available_sessions: List[SessionInfo]


class SessionResponse(BaseModel):
    """
    Modello di risposta per la creazione o il join di una sessione.

    Attributes
        db_session_id (int): ID della sessione registrata nel database.
        room_name (str): Nome della stanza associata alla sessione.
        session_uuid (UUID): Identificativo univoco della sessione lato server.
        mode (str): Modalità di gioco (es. 'single', 'multi').
    """
    db_session_id: int
    room_name: str
    session_uuid: UUID
    mode: str
