from pydantic import BaseModel

class LoginRequest(BaseModel):
    """
    Schema della richiesta di login.

    Attributes
        identifier (str): Identificatore dell'utente, può essere username o email.
        password (str): Password in chiaro inserita dall'utente.
    """
    identifier: str  # può essere username o email
    password: str

class LoginResponse(BaseModel):
    """
    Schema della risposta al login.

    Attributes
        status (str): Stato del login, ad esempio "ok" o "error".
    """
    status: str