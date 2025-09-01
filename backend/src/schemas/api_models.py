from pydantic import BaseModel
from typing import Optional

class ResponseAPI(BaseModel):
    """Schema di risposta dell'API LLM.

    Attributes
        answer (str): Risposta generata dal modello LLM.
        chat_history (list[dict]): Cronologia della conversazione,
            in formato lista di dizionari con chiavi 'role' e 'content'.
    """
    answer: str
    chat_history: list[dict]

class RequestAPI(BaseModel):
    """Schema per inviare una richiesta al modello LLM.

    Attributes
        question (str): Domanda posta dall'utente al modello.
    """
    question: str

class SimilarityResponse(BaseModel):
    """Schema di risposta per la ricerca di frasi simili.

    Attributes
        frase_input (str): La frase fornita dall'utente.
        frase_simile (Optional[str]): La frase più simile trovata nel database.
            Se non è stata trovata alcuna frase simile, sarà `None`.
        risposta_trovata (str): La risposta associata (umana o LLM).
        similarita (float): Punteggio di similarità coseno tra 0.0 e 1.0.
        tipo_risposta (str): Origine della risposta:
            - `"HUMAN"` → risposta trovata da un altro utente
            - `"LLM"` → risposta generata dal modello
    """
    frase_input: str
    frase_simile: Optional[str] = None  # ora può essere None
    risposta_trovata: str
    similarita: float
    tipo_risposta: str