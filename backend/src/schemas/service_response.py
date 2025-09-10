from pydantic import BaseModel

class ServiceResponse(BaseModel):
    """
    Schema generico per la risposta di un servizio.

    Attributes
        status (str): Stato della risposta del servizio.
            Può essere:
            - `"ok"` → operazione completata con successo
            - `"error"` → si è verificato un errore durante l'operazione
    """
    status: str             