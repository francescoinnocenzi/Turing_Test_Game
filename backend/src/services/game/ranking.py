import websocket
from database.connection import create_db_connection
from fastapi import HTTPException, Depends
import mariadb
from fastapi import WebSocket
from typing import List
from schemas.ranking import RankingEntry, RankingResponse
from services.game.session import get_data_session_http
from services.instances.cookie import cookie
from fastapi_sessions.backends.implementations import InMemoryBackend
from schemas.session_data import SessionData
from services.instances.session_backend import backend
from uuid import UUID
from fastapi import Request

async def get_ranking(request: Request, session_uuid: UUID) -> RankingResponse:
    """
    Recupera la classifica dei giocatori basata sui punteggi totali.

    Returns
        RankingResponse: Oggetto contenente la lista dei top 10 giocatori con punteggio.
    
    Raises
        HTTPException: Se c'è un errore nel recupero dei dati dal database.
    """
    conn = create_db_connection()
    cursor = conn.cursor()

    try:
        # Recupera la classifica dei primi 10 giocatori
        cursor.execute("""
            SELECT u.username, SUM(s.score) as total_score
            FROM scores s
            JOIN users u ON s.user_id = u.id
            WHERE s.mode = ?
            GROUP BY s.user_id
            ORDER BY total_score DESC
            LIMIT 10
        """, ("MULTIPLAYER",))

        results = cursor.fetchall()
        ranking: List[RankingEntry] = [RankingEntry(username=row[0], total_score=row[1]) for row in results]

        # Recupera user_id da SessionData
        session_id, user_id = await get_data_session_http(session_uuid, backend)
        if not user_id:
            raise HTTPException(status_code=404, detail="Utente non trovato")

        # Recupera il punteggio dell'utente loggato
        cursor.execute("""
            SELECT u.username, COALESCE(SUM(s.score), 0) as total_score
            FROM scores s
            JOIN users u ON s.user_id = u.id 
            WHERE s.mode = ? AND u.id = ? 
            GROUP BY s.user_id
            ORDER BY total_score DESC
            LIMIT 10
        """, ("MULTIPLAYER", user_id))

        row = cursor.fetchone()
        my_score = row[1] if row else 0

        return RankingResponse(ranking=ranking, my_score=my_score)

    except mariadb.Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()
