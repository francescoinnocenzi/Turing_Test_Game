from schemas.question import QuestionRequest, QuestionResponse
from schemas.answer import AnswerRequest
from services.llm.transformer import get_model
from database.connection import create_db_connection
import json
import mariadb
from fastapi import HTTPException
from services.game.answers import create_answer
from services.llm.generate_answer import get_llm_response
from services.instances.manager import manager


def create_question(request: QuestionRequest):
    conn = create_db_connection()
    cursor = conn.cursor()
    model = get_model()  # carichi il modello solo una volta (lazy loading)
    
    try:
        # 1. Calcolo embedding della domanda
        embedding = model.encode(request.text).tolist()
        embedding_json = json.dumps(embedding)  # serializzo in stringa JSON

        # 2. Inserisco domanda + embedding
        cursor.execute("""
            INSERT INTO questions (session_id, text, author_user_id, author_type, room_name, embedding) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            request.session_id,
            request.text,
            request.author_user_id,
            request.author_type,
            request.room_name,
            embedding_json
        ))
        conn.commit()

        question_id = cursor.lastrowid

        # 3. Ritorno la domanda creata (senza embedding per non appesantire la response)
        cursor.execute("""
            SELECT id, session_id, text, author_user_id, room_name, created_at
            FROM questions
            WHERE id = ?
        """, (question_id,))
        row = cursor.fetchone()

        return QuestionResponse(
            id=row[0], 
            session_id=row[1], 
            text=row[2],
            author_user_id=row[3], 
            room_name=row[4], 
            created_at=row[5]
        )

    except mariadb.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

  
#Gestione caso domanda automatica in singleplayer
async def process_auto_question(room_name, websocket, question, session_id):
    q_req = QuestionRequest(
        text=question,
        room_name=room_name,
        author_user_id=None,
        author_type="BOT",
        session_id=session_id
    )
    saved_q = create_question(q_req)

     #Ivia domanda ai player (Uno è il giocatore l'altro è il bot)
    await manager.send_question_to_players(question, room_name, saved_q.id)

    #Risposta del bot alla domanda del ULLM
    bot_resp = await get_llm_response(question)
    create_answer(AnswerRequest(
        question_id=saved_q.id,
        session_id=session_id,
        text=bot_resp,
        author_user_id=None,
        author_type="BOT",
        room_name=room_name
    ))
    await manager.send_answer_to_judge(bot_resp, room_name, "BOT")
    print(f"🤖 BOT-AUTO answer sent: {bot_resp}")
    
