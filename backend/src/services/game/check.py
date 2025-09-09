from fastapi import HTTPException
from services.llm.generate_judgment import get_llm_judgment
from services.llm.generate_question import auto_generate_next_question
from services.game.scores import handle_scores
from services.instances.manager import manager
from database.connection import create_db_connection
import services.state as state

from typing import Any

async def check_all_answered(question_id: int, room_name: str, session_id: int, role: str, mode: str, user_id: int) -> None:
    """
    Notifica il giudice quando tutti i player hanno risposto e, se necessario,
    genera automaticamente la prossima domanda in modalità single.

    Args
        question_id (int): ID della domanda corrente.
        room_name (str): Nome della stanza.
        session_id (int): ID della sessione.
        role (str): Ruolo del player (es. 'HUMAN', 'JUDGE').
        mode (str): Modalità di gioco ('single' o 'multi').

    Returns
        None

    Raises:
        Exception: Propaga eventuali errori generati durante l'accesso al database
          o nell'invio dei messaggi tramite WebSocket.
    """
    try:
        conn = create_db_connection()
        cursor = conn.cursor()

        # Conta le domande per la sessione
        cursor.execute("SELECT COUNT(*) FROM questions WHERE session_id = ?", (session_id,))
        question_count = cursor.fetchone()[0]

        MAX_QUESTIONS = 1  # Configurabile

        # Conta risposte per la domanda corrente
        cursor.execute("""
            SELECT COUNT(*) as total_answers
            FROM answers 
            WHERE question_id = ?
        """, (question_id,))

        total_answers = cursor.fetchone()[0]
        print(f"Risposte ricevute: {total_answers}/2")

        if total_answers >= 2:  # Entrambi hanno risposto
            print("Tutti hanno risposto!")
            await manager.send_to_judge({ 
                "type": "all_answered", 
                "message": "Tutti hanno risposto! Puoi inviare la prossima domanda." 
            }, room_name)

            if role == "PLAYER" and mode == "single" and question_count < MAX_QUESTIONS:
                await auto_generate_next_question(room_name, session_id)
            
            if question_count >= MAX_QUESTIONS:
                await check_and_finalize_game(session_id, room_name, question_count, MAX_QUESTIONS, role, mode, user_id)

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Errore in check_all_answered: {e}")


async def check_and_finalize_game(session_id: int, room_name: str, question_count: int, max_questions: int, role: str, mode: str, user_id: int) -> None:
    """
    Controlla se il numero massimo di domande è stato raggiunto e, se sì,
    esegue il giudizio finale e notifica i giocatori.

    Args
        session_id (int): ID della sessione corrente.
        room_name (str): Nome della stanza.
        question_count (int): Numero di domande già poste.
        max_questions (int): Numero massimo di domande per la sessione.
        role (str): Ruolo dell'utente ('HUMAN' o 'JUDGE').
        mode (str): Modalità di gioco ('single' o 'multi').

    Returns
        None

    Raises
        HTTPException: Se i risultati del giudizio LLM non sono validi.
        Exception: Propaga altri errori generici durante l'invio dei messaggi.
    """

    # Caso giudice LLM
    if mode == "single" and role == "PLAYER":
        # Fine partita - esegui giudizio
        judgment_result = await get_llm_judgment(session_id)

        #Aggiusto punteggi
        if judgment_result.judge_result == "GIUDICE ha VINTO":
            print(f"GIUDICE LLM ha indovinato con user {user_id}")
            handle_scores(user_id=user_id, session_id=session_id, mode="single",role=role, win=True) 
        elif judgment_result.judge_result == "GIUDICE ha PERSO":
            print(f"GIUDICE LLM ha sbagliato con user {user_id}")
            handle_scores(user_id=user_id, session_id=session_id, mode="single",role=role, win=False)
        else:
            raise HTTPException(status_code=500, detail="Errore nei punteggi del giudizio LLM")
        # Invia risultato finale
        print(f"GIUDIZIO {judgment_result}")
        
        # Invia il giudizio a tutti i client
        await manager.send_judgment_to_all(judgment_result.judge_result, room_name)
        print(f"Giudizio inviato: {judgment_result.judge_result}")
    
    if (mode == "single" or mode == "multi"):
        await manager.send_message_to_all("Scegli chi è UMANO", "time_to_judge", room_name)