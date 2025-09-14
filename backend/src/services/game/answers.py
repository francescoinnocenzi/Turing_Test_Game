from schemas.answer import AnswerRequest, AnswerResponse
from database.connection import create_db_connection
import json
import mariadb
from fastapi import HTTPException
from typing import Any
from fastapi import HTTPException
import mariadb

def create_answer(request: AnswerRequest) -> AnswerResponse:
    """
    Inserisce una nuova risposta nel database e restituisce i dati completi della risposta appena creata.

    Args
        request (AnswerRequest): Oggetto contenente i dati della risposta da inserire

    Returns
        AnswerResponse: Oggetto contenente i dati completi della risposta inserita.

    Raises
        HTTPException: In caso di errore nel database.
    """
    conn: mariadb.Connection = create_db_connection()
    cursor: mariadb.Cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO answers (question_id, session_id, text, author_user_id, author_type, room_name) 
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                request.question_id,
                request.session_id,
                request.text,
                request.author_user_id,
                request.author_type,
                request.room_name
            )
        )
        conn.commit()

        answer_id: int = cursor.lastrowid

        cursor.execute(
            """
            SELECT id, question_id, session_id, text, author_user_id, author_type, room_name, created_at
            FROM answers
            WHERE id = ?
            """,
            (answer_id,)
        )
        row: Any = cursor.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Domanda non trovata dopo l'inserimento")

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
