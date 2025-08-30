from database.connection import create_db_connection
from fastapi import HTTPException
from fastapi import Response, Depends
from uuid import UUID
from fastapi_sessions.frontends.implementations import SessionCookie, CookieParameters
from schemas.session_data import SessionData
from fastapi_sessions.backends.implementations import InMemoryBackend
from services.cookie import cookie
import mariadb

async def create_session(response: Response, backend: InMemoryBackend[UUID, SessionData], session_uuid: UUID):
    global previous_questions
    global chat_history

    print("📦 Stato backend inizio create session: %s", backend.data)

    # Resetto le liste a ogni sessione
    chat_history = []
    previous_questions = []

    conn = create_db_connection()
    cursor = conn.cursor()
    import uuid
    try:
        # usa room_name scelto dall’utente
        # room_name = req.room_name.strip()

        # genera un nome univoco della stanza
        room_name = f"room_{uuid.uuid4().hex[:6]}"

        # verifica che non esista già
        cursor.execute("SELECT id FROM sessions WHERE room_name = ?", (room_name,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Nome stanza già usato")

        cursor.execute("INSERT INTO sessions (room_name) VALUES (?)", (room_name,))
        conn.commit()
        db_session_id = cursor.lastrowid

        # aggiorna SessionData
        old_data = await backend.read(session_uuid)
        print("📌 old_data trovato:", old_data)
        if not old_data:
            raise HTTPException(status_code=404, detail="Session not found")

        updated = old_data.model_copy(update={"session_id": db_session_id})
        await backend.update(session_uuid, updated)

        return {
            "status": "Success",
            "db_session_id": db_session_id,
            "room_name": room_name,
            "session_uuid": str(session_uuid),
        }

    except mariadb.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

async def join_session(room_name: str, backend: InMemoryBackend[UUID, SessionData], session_uuid: UUID = Depends(cookie)):
    conn = create_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM sessions WHERE room_name = ?", (room_name,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Partita non trovata")
        db_session_id = row[0]

        # aggiorno SessionData del player
        old_data = await backend.read(session_uuid)
        if not old_data:
            raise HTTPException(status_code=404, detail="User session not found")

        updated = old_data.model_copy(update={"session_id": db_session_id})
        await backend.update(session_uuid, updated)

        # chiudo la stanza: non è più disponibile per altri player
        cursor.execute("UPDATE sessions SET is_available = ? WHERE id = ?", (False, db_session_id))
        conn.commit()

        return {
            "status": "Success",
            "db_session_id": db_session_id,
            "room_name": room_name,
            "session_uuid": str(session_uuid),
        }

    finally:
        cursor.close()
        conn.close()

async def available_sessions():
    conn = create_db_connection()
    cursor = conn.cursor()
    try:
        # 🔹 Pulisce le stanze vecchie (più di 120 secondi)
        cursor.execute("""
            UPDATE sessions
            SET is_available = FALSE
            WHERE is_available = TRUE
              AND TIMESTAMPDIFF(SECOND, created_at, NOW()) >= 120
        """)
        conn.commit()

        # 🔹 Prende solo le stanze ancora disponibili
        cursor.execute("""
            SELECT id, room_name, created_at 
            FROM sessions 
            WHERE is_available = TRUE
            ORDER BY created_at DESC
        """)
        rows = cursor.fetchall()

        sessions = [
            {"id": row[0], "room_name": row[1], "created_at": row[2].isoformat()}
            for row in rows
        ]

        return {"available_sessions": sessions}

    finally:
        cursor.close()
        conn.close()