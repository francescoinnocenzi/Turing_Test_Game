from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class JudgmentRequest(BaseModel):
    """
    Schema della richiesta di giudizio da parte di un giudice.

    Attributes
        session_id (int): ID della sessione in cui avviene il giudizio.
        judge_id (int): ID del giudice che emette il giudizio.
        chosen_player_human (str): Identificatore o username del player umano scelto.
    """
    session_id: int
    judge_id: int
    chosen_player_human: str  

class JudgmentResponse(BaseModel):
    """
    Schema di risposta dopo la creazione di un giudizio.

    Attributes
        id (int): ID univoco del giudizio.
        session_id (int): ID della sessione di riferimento.
        judge_id (int): ID del giudice che ha emesso il giudizio.
        chosen_player_human (str): Identificatore o username del player umano scelto.
        created_at (datetime): Data e ora di creazione del giudizio.
    """
    id: int
    session_id: int
    judge_id: int
    chosen_player_human: str
    created_at: datetime 

class LLMJudgmentResponse(BaseModel):
    """
    Schema di risposta quando il giudizio proviene dal modello LLM.

    Attributes
        judgment (str): Giudizio prodotto dal modello LLM.
        human_result (str): Valutazione o risultato relativo al giocatore umano.
    """
    judgment: str
    human_result: str
