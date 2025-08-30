from schemas.answer import AnswerRequest, AnswerResponse
from database.connection import create_db_connection
import json
import mariadb
from fastapi import HTTPException

def create_answer(request: AnswerRequest):
    conn = create_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO answers (question_id, session_id, text, author_user_id, author_type, room_name) 
            values (?, ?, ?, ?, ?, ?)
        """, (request.question_id, request.session_id, request.text, request.author_user_id, request.author_type, request.room_name))
        conn.commit()

        answer_id = cursor.lastrowid

        cursor.execute("""
            SELECT id, question_id, session_id, text, author_user_id, author_type, room_name, created_at
            FROM answers
            where id = ?
        """, (answer_id, ))
        # Restituisce solo la prima riga
        row = cursor.fetchone()

        return AnswerResponse(
            id=row[0],
            question_id=row[1],
            session_id=row[2],
            text=row[3],
            author_user_id=row[4],
            author_type=row[5],
            room_name=row[6],
            created_at=row[7]
        )

    except mariadb.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()