from schemas.judgment import JudgmentRequest, JudgmentResponse
from database.connection import create_db_connection
from fastapi import HTTPException
import mariadb
def create_judgment(request: JudgmentRequest) -> JudgmentResponse:
    """
    Salva un giudizio nel database e restituisce il record creato.

    Args
        request (JudgmentRequest): Dati del giudizio da salvare.

    Returns
        JudgmentResponse: Record del giudizio appena creato.
    """
    conn = create_db_connection()
    cursor = conn.cursor()

    try:
        # Salva il giudizio
        cursor.execute("""
            INSERT INTO judgments (session_id, judge_id, chosen_player_human)
            VALUES (?, ?, ?)
        """, (request.session_id, request.judge_id, request.chosen_player_human))
        conn.commit()

        judgment_id = cursor.lastrowid

        # Recupera il record appena salvato
        cursor.execute("""
            SELECT id, session_id, judge_id, chosen_player_human, created_at
            FROM judgments
            WHERE id = ?
        """, (judgment_id,))
        row = cursor.fetchone()

        return JudgmentResponse(
            id=row[0],
            session_id=row[1],
            judge_id=row[2],
            chosen_player_human=row[3],
            created_at=row[4]
        )

    except mariadb.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()
