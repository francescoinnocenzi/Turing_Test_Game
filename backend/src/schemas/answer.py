from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AnswerRequest(BaseModel):
    """Schema per la richiesta di creazione di una risposta.

    Attributes
        question_id (int): ID della domanda a cui si riferisce la risposta.
        session_id (int): ID della sessione corrente.
        text (str): Testo della risposta.
        author_user_id (int | None): ID dell’utente che ha scritto la risposta
            (None se il mittente è un bot).
        author_type (str): Tipo di autore della risposta. Può essere:
            - `"HUMAN"` → risposta scritta da un utente
            - `"BOT"` → risposta generata dal modello
        room_name (str): Nome della stanza in cui è stata data la risposta.
    """
    question_id: int
    session_id: int
    text: str
    author_user_id: int | None
    author_type: str  # 'HUMAN' or 'BOT'
    room_name: str

class AnswerResponse(BaseModel):
    """Schema di risposta restituito dopo la creazione/recupero di una risposta.

    Attributes:
        id (int): ID univoco della risposta.
        question_id (int): ID della domanda a cui appartiene la risposta.
        session_id (int): ID della sessione in cui è stata data la risposta.
        text (str): Testo della risposta.
        author_user_id (int | None): ID dell’utente autore (None se bot).
        author_type (str): Tipo di autore (`"HUMAN"` o `"BOT"`).
        room_name (str): Nome della stanza di riferimento.
        created_at (datetime): Timestamp di creazione della risposta.
    """
    id: int
    question_id: int
    session_id: int
    text: str
    author_user_id: int | None
    author_type: str
    room_name: str
    created_at: datetime
