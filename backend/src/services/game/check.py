from fastapi import HTTPException
from services.llm.generate_judgment import get_llm_judgment
from services.llm.generate_question import auto_generate_next_question
from services.game.scores import handle_scores
from services.instances.manager import manager
from database.connection import create_db_connection
from services.state import user_id

async def check_all_answered(question_id: int, room_name: str, session_id: int, role: str, mode: str):
    """Verifica se tutti i player hanno risposto alla domanda"""
    try:
        conn = create_db_connection()
        cursor = conn.cursor()

        # Conta domande per questa sessione
        cursor.execute("""
            SELECT COUNT(*) FROM questions 
            WHERE session_id = ?
        """, (session_id,))

        question_count = cursor.fetchone()[0]
        MAX_QUESTIONS = 2  # Configurabile

        await check_and_finalize_game(session_id, room_name, question_count, MAX_QUESTIONS, role, mode)
        
        cursor.execute("""
            SELECT COUNT(*) as total_answers,
                   COUNT(CASE WHEN author_type = 'HUMAN' THEN 1 END) as human_answers,
                   COUNT(CASE WHEN author_type = 'BOT' THEN 1 END) as bot_answers
            FROM answers 
            WHERE question_id = ?
        """, (question_id,))
        
        result = cursor.fetchone()
        total_answers, human_answers, bot_answers = result
        
        print(f"Risposte ricevute: {total_answers}/2 (Human: {human_answers}, Bot: {bot_answers})")
        
        if total_answers >= 2:  # Entrambi hanno risposto
            print("✅ Tutti hanno risposto!")
            await manager.send_to_judge({ 
                "type": "all_answered", 
                "message": "✅ Tutti hanno risposto! Puoi inviare la prossima domanda." 
                }, room_name)
            
            if role == "HUMAN" and mode == "single" and question_count < MAX_QUESTIONS:
                await auto_generate_next_question(room_name, session_id)
            
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Errore in check_all_answered: {e}")

async def check_and_finalize_game(session_id: int, room_name: str, question_count: int, max_questions: int, role: str, mode: str):
    """
    Controlla se il numero massimo di domande è stato raggiunto
    e in caso affermativo esegue il giudizio finale e chiude la partita.
    """
    if question_count >= max_questions:

        if mode == "single" and role == "HUMAN":
            # Fine partita - esegui giudizio
            judgment_result = await get_llm_judgment(session_id)

            #Aggiusto punteggi
            if judgment_result.get("human_result") == "HUMAN ha PERSO":
                print("✅ GIUDICE LLM ha indovinato (Player ha perso)! ")
                handle_scores(user_id=user_id, session_id=session_id, mode="single",role=role, win=False) 
            elif judgment_result.get("human_result") == "HUMAN ha VINTO":
                print("✅ GIUDICE LLM ha sbagliato (Player ha vinto)! ")
                handle_scores(user_id=user_id, session_id=session_id, mode="single",role=role, win=True)
            else:
                raise HTTPException(status_code=500, detail="Errore nei punteggi del giudizio LLM")
            # Invia risultato finale
            print(f"GIUDIZIO {judgment_result}")
            
            if "judgment" in judgment_result:
                # Invia il giudizio a tutti i client
                await manager.send_judgment_to_all(judgment_result["human_result"], room_name)
                print(f"Giudizio inviato: {judgment_result['human_result']}")
            else:
                print(f"Errore nel giudizio: {judgment_result.get('error', 'Errore sconosciuto')}")
        
        if (mode == "single" or mode == "multi") and role == "JUDGE":
            await manager.send_message_to_all("Scegli chi è UMANO", "time_to_judge", room_name)