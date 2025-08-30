from schemas.question import QuestionRequest
from schemas.answer import AnswerRequest
from services.questions import create_question
from services.answers import create_answer
import json
from services.llm.generate_answer import get_llm_response
from services.llm.generate_answer import trova_simile
from services.manager import manager
from services.game.check import check_all_answered

#Gestione della domanda in arrivo (singleplayer)
async def handle_question(room_name, client_id, websocket, role, message, mode, session_id, user_id):
    text = message.get("text")
    print(f"❓ Domanda dal giudice {client_id}: {text}")
    
    # Salva domanda
    q_req = QuestionRequest(
        text=text,
        room_name=room_name,
        author_user_id=user_id,
        session_id=session_id,
        author_type="HUMAN"
    )
    saved_q = create_question(q_req)

    await websocket.send_text(json.dumps({
        "type": "question_saved",
        "question_id": saved_q.id
    }))
    # Invia domanda a players (caso multiplayer)
    await manager.send_question_to_players(text, room_name, saved_q.id)
    print(f"Question sent to players in room {room_name}")

    # BOT 1 (LLM)
    bot1_resp = await get_llm_response(text)
    #Salva risposta bot 
    create_answer(AnswerRequest(
        question_id=saved_q.id,
        session_id=session_id,
        text=bot1_resp,
        author_user_id=None,
        author_type="BOT",
        room_name=room_name
    ))
    await manager.send_answer_to_judge(bot1_resp, room_name, 2)
    print(f" BOT-LLM answer sent: {bot1_resp}")  
    
    if mode == "single":
        # BOT 2 (retrieval o fallback LLM)
        bot2_data = await trova_simile(q_req)
        bot2_resp = bot2_data["risposta_trovata"]
        
        #Salva risposta bot retrival solo se generata da LLM (perche HUMAN è gia presente nel DB)

        create_answer(AnswerRequest(
            question_id=saved_q.id,
            session_id=session_id,
            text=bot2_resp,
            author_user_id=None,
            author_type="BOT_AS_HUMAN" if bot2_data["tipo_risposta"] == "LLM" else "HUMAN",
            room_name=room_name
        ))
        await manager.send_answer_to_judge(bot2_resp, room_name, 1) #metto 1 perche risponde al posto di HUMAN
        print(f" BOT-Retrieval answer sent: {bot2_resp}")  # <-- log

    await check_all_answered(saved_q.id, room_name, session_id=session_id, role="JUDGE", mode=mode)

#Gestione della risposta inviata singleplayer
async def handle_answer(room_name, client_id, websocket, role, message, mode, session_id, user_id):
    print("RISPOSTA ARRIVATA:",{"role": role, "message": message, "mode": mode})
    print(f"QUESTION_ID in handle_answer: {message.get('question_id')}") # stampa None
    text = message.get("text")
    question_id = message.get("question_id")

    player_number = 1 if role == "HUMAN" else 2
    print(f" Risposta da {role} (client {client_id}): {text} mode : {mode}")

    await manager.send_answer_to_judge(text, room_name, player_number)

    # in realtà id lo recupera qua come quello più recente non vabbene
    # if not question_id:
    #     conn = create_db_connection()
    #     cur = conn.cursor()
    #     cur.execute("""
    #         SELECT id FROM questions 
    #         WHERE room_name = ? 
    #         ORDER BY created_at DESC 
    #         LIMIT 1
    #     """, (room_name,))
    #     last_q = cur.fetchone()
    #     cur.close(); conn.close()
    #     if last_q:
    #         question_id = last_q[0]

    if question_id:
        create_answer(AnswerRequest(
            question_id=question_id,
            session_id=session_id,
            text=text,
            author_user_id=user_id,
            author_type=role,
            room_name=room_name
        ))
    
    # Usa la funzione centralizzata per verificare se tutti hanno risposto
    await check_all_answered(question_id, room_name, session_id=session_id, role=role, mode=mode)

async def handle_raw_text(room_name, client_id, role, text, mode, session_id):
    print(f" Raw text da {role}: {text}")
    if role == "JUDGE":
        await handle_question(room_name, client_id, role, {"text": text}, None, mode, session_id=session_id)
    else:
        await handle_answer(room_name, client_id, role, {"text": text}, None, mode, session_id=session_id)