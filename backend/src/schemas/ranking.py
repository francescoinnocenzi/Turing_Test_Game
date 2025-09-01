
from pydantic import BaseModel

class RankingEntry(BaseModel):
    """
    Rappresenta un singolo elemento della classifica.

    Attributes
        username (str): Nome utente del giocatore.
        total_score (int): Punteggio totale accumulato dal giocatore.
    """
    username: str
    total_score: int

class RankingResponse(BaseModel):
    """
    Risposta contenente la classifica dei giocatori.

    Attributes
        ranking (list[RankingEntry]): Lista ordinata di giocatori con i rispettivi punteggi.
    """
    ranking: list[RankingEntry]