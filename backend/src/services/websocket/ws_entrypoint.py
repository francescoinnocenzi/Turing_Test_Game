from fastapi import WebSocket
from fastapi_sessions.frontends.implementations import SessionCookie, CookieParameters
from services.websocket.websocket import ConnectionManager
import json
from fastapi import WebSocket
from fastapi_sessions.backends.implementations import InMemoryBackend
from uuid import UUID
from schemas.session_data import SessionData
from schemas.judgment import JudgmentRequest
from services.game.handle import handle_question, handle_answer, handle_message
from services.llm.generate_question import auto_generate_next_question
from services.game.judgment import create_judgment
from services.game.judgment import create_judgment
from services.game.scores import handle_scores
from services.game.session import setup_session
from services.game.handle import handle_message
from fastapi import WebSocketDisconnect
from services.game.handle import handle_raw_text
from services.instances.session_backend import backend
from services.game.handle import assign_and_send_positions
import services.state as state
from fastapi import WebSocket, WebSocketDisconnect
from fastapi_sessions.backends.implementations import InMemoryBackend
from uuid import UUID

async def ws_entrypoint(websocket: WebSocket, room_name: str, client_id: str, cookie, backend: InMemoryBackend[UUID, SessionData],manager) -> None:
    """
    Gestisce la connessione WebSocket di un client.

    Args
        websocket (WebSocket): Connessione WebSocket del client.
        room_name (str): Nome della stanza.
        client_id (str): Identificatore univoco del client.
        cookie: Funzione per recuperare il cookie di sessione.
        backend (InMemoryBackend[UUID, SessionData]): Backend per gestire le sessioni.
        manager: Oggetto che gestisce la logica dei messaggi e delle stanze.

    Workflow
        - Recupera ruolo e modalità dai parametri della query.
        - Verifica la sessione e ottiene session_id e user_id.
        - Connette il client tramite il manager.
        - Se il client è HUMAN in modalità single, genera automaticamente la prossima domanda.
        - Loop infinito per ricevere messaggi:
            - Se il messaggio è JSON valido, chiama `handle_message`.
            - Se non è JSON, chiama `handle_raw_text`.
        - Gestisce la disconnessione del client.

    Returns
        None
    """
    role = websocket.query_params.get("role", "SPECTATOR").upper()
    mode = websocket.query_params.get("mode", "single").lower()

    print(f"Cookie disponibili: {websocket.cookies}")
    session_id, user_id = await setup_session(websocket, cookie, backend)
    print(f"SESSION_ID FINALE: {session_id}")

    await manager.connect(room_name, websocket, client_id, role)
    print(f"Nuovo client {client_id} connesso come {role} in modalità {mode}")

    if role == "HUMAN" and mode == "single":
        await auto_generate_next_question(room_name, session_id)

    try:
        while True:
            data = await websocket.receive_text()
            ws = manager.rooms[room_name][client_id]
            role = ws["role"]

            try:
                message = json.loads(data)
                msg_type = message.get("type")
                print(f"Messaggio ricevuto: {message}")

                await handle_message(
                    msg_type, room_name, websocket, role, message,
                    mode, session_id, user_id, manager
                )

            except json.JSONDecodeError:
                await handle_raw_text(room_name, client_id, role, data, mode, session_id=session_id)

    except WebSocketDisconnect:
        manager.disconnect(room_name, client_id)
        await manager.broadcast(f"Client #{client_id} left {room_name}", room_name)
        await manager.notify_players_update(room_name)


