from pydantic import BaseModel

class RegisterRequest(BaseModel):
    """
    Richiesta per la registrazione di un nuovo utente.

    Attributes
        username (str): Nome utente.
        email (str): Indirizzo email dell'utente.
        password (str): Password in chiaro fornita in fase di registrazione.
    """
    username: str
    email: str
    password: str

class RegisterResponse(BaseModel):
    """
    Risposta alla richiesta di registrazione.

    Attributes
        status (str): Stato dell'operazione.
    """
    status: str