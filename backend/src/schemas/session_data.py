from pydantic import BaseModel

class SessionData(BaseModel):
    """
    Dati relativi alla sessione utente.

    Attributes
        user_id (int): ID dell'utente loggato.
        session_id (int | None): ID della sessione attiva.
    """
    user_id: int # id user_logato
    session_id: int | None = None
