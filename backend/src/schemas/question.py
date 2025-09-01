from pydantic import BaseModel
from datetime import datetime

class QuestionRequest(BaseModel):
    """
    Schema della richiesta per creare una nuova domanda.

    Attributes
        session_id (int): Identificativo univoco della sessione di gioco.
        text (str): Testo della domanda posta.
        author_user_id (int | None): ID dell'utente autore della domanda, 
            può essere None se la domanda è generata da un bot.
        author_type (str): Tipo di autore della domanda, ad esempio 'HUMAN' o 'BOT'.
        room_name (str): Nome della stanza in cui viene posta la domanda.
    """
    session_id: int
    text: str
    author_user_id: int | None
    author_type: str
    room_name: str

class QuestionResponse(BaseModel):
    """
    Schema della risposta contenente i dettagli di una domanda salvata.

    Attributes
        id (int): Identificativo univoco della domanda.
        text (str): Testo della domanda.
        session_id (int): ID della sessione di gioco a cui appartiene la domanda.
        author_user_id (int | None): ID dell'utente autore della domanda.
        room_name (str): Nome della stanza associata alla domanda.
        created_at (datetime): Data e ora di creazione della domanda.
    """
    id: int
    text: str
    session_id: int
    author_user_id: int | None
    room_name: str
    created_at: datetime
