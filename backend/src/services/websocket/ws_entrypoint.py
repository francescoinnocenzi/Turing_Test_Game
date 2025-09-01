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

'''
async def ws_entrypoint(websocket: WebSocket, room_name: str, client_id: int, cookie: CookieParameters, backend: InMemoryBackend[UUID, SessionData], manager: ConnectionManager):
    #Prendo parametri dalla query string
    role = websocket.query_params.get("role", "SPECTATOR").upper()
    mode = websocket.query_params.get("mode", "single").lower()

    # DEBUG: Stampa TUTTI i cookie disponibili
    # websocket.cookies è un dizionario contenente tutti i cookie che il client ha inviato con la connessione WebSocket.
    print(f"🍪 Tutti i cookie disponibili: {websocket.cookies}")

    session_id = None
    
    try:
        session_uuid = cookie(websocket) # legge il cookie di sessione impostato e restituisce il UUID della sessione.
        print(f"✅ Session UUID verificato: {session_uuid}")
        
        # Cerca nel backend in memoria i dati salvati per quella sessione.
        stored_data: SessionData = await backend.read(session_uuid) 
        
        if stored_data:
            session_id = stored_data.session_id
            user_id = stored_data.user_id

        else:
            print("Dati sessione non trovati")
            
    except Exception as e:
        print(f"Errore verifica sessione: {e}")
       

    print(f"SESSION_ID FINALE: {session_id}")

    await manager.connect(room_name, websocket, client_id, role)
    print(f"✅ Nuovo client {client_id} connesso come {role} in modalità {mode}")

    # Se è PLAYER in singleplayer → genera subito una domanda
    if role == "HUMAN" and mode == "single": #Single player modalita role = HUMAN
        question = await auto_generate_next_question(room_name, session_id) #Genero domanda dall'LLM
        # if question:
        #     await process_auto_question(room_name, websocket, question, session_id) #Processo domanda automatica

    try:
        while True:
            data = await websocket.receive_text()
            ws = manager.rooms[room_name][client_id]
            role = ws["role"]

            try:
                message = json.loads(data)
                msg_type = message.get("type")

                print(f"📥 Messaggio ricevuto da client {message} {msg_type}")

                if mode == "single":
                    if msg_type == "question": #Gestione della domanda in arrivo
                        await handle_question(room_name, client_id, websocket, role, message, mode, session_id, user_id)

                    elif msg_type == "answer": #Gestione della riposta in arrivo
                        await handle_answer(room_name, client_id, websocket, role, message, mode, session_id, user_id)
                    
                    elif msg_type == "judge_choice":
                        chosen_player_human = message.get("chosen_player_human")   # "A" oppure "B"
                        
                        print("📥 Giudizio ricevuto:", chosen_player_human)

                        judgment_req = JudgmentRequest(
                            session_id=session_id,
                            judge_id=user_id,
                            chosen_player_human=chosen_player_human
                        )

                        result_judgment = create_judgment(judgment_req)
                        judge_choice = result_judgment.chosen_player_human  # "A" o "B"


                        # Recupera posizioni reali dal dict globale
                        positions = state.room_positions.get(room_name)

                        if not positions:
                            print("⚠️ ERRORE: posizioni non trovate per la room")
                            return

                        # Mappa scelta A/B a left/right
                        if judge_choice == "A":
                            chosen_type = positions["left"]["type"]
                        else:  # judge_choice == "B"
                            chosen_type = positions["right"]["type"]

                        # Verifica se il tipo scelto era HUMAN
                        correct_answer = (chosen_type == "HUMAN")

                        print(f"SCELTA FRONTEND: {judge_choice} → {chosen_type}")

                        if correct_answer:
                            correct_guess = "GIUDICE ha VINTO"
                            handle_scores(user_id, session_id, mode, role=role, win=True)
                            await manager.send_judgment_to_all(correct_guess, room_name)
                        else:
                            correct_guess = "GIUDICE ha PERSO"
                            handle_scores(user_id, session_id, mode, role=role, win=False)
                            await manager.send_judgment_to_all(correct_guess, room_name)

                    
                elif mode == "multi":
                    if msg_type == "question":
                        await handle_question(room_name, client_id, websocket, role, message, mode, session_id, user_id)

                    elif msg_type == "answer":
                        await handle_answer(room_name, client_id, websocket, role, message, mode, session_id, user_id)


                    elif msg_type == "judge_choice":

                        chosen_player_human = message.get("chosen_player_human")   # "A" oppure "B"
                        
                        print("📥 Giudizio ricevuto:", chosen_player_human)

                        judgment_req = JudgmentRequest(
                            session_id=session_id,
                            judge_id=user_id,
                            chosen_player_human=chosen_player_human
                        )

                        result_judgment = create_judgment(judgment_req)
                        judge_choice = result_judgment.chosen_player_human  # "A" o "B"


                        # Recupera posizioni reali dal dict globale
                        positions = state.room_positions.get(room_name)

                        if not positions:
                            print("⚠️ ERRORE: posizioni non trovate per la room")
                            return

                        # Mappa scelta A/B a left/right
                        if judge_choice == "A":
                            chosen_type = positions["left"]["type"]
                        else:  # judge_choice == "B"
                            chosen_type = positions["right"]["type"]

                        # Verifica se il tipo scelto era HUMAN
                        correct_answer = (chosen_type == "HUMAN")

                        print(f"SCELTA FRONTEND: {judge_choice} → {chosen_type}")

                        if correct_answer:
                            correct_guess = "GIUDICE ha VINTO"
                            handle_scores(user_id, session_id, mode, role=role, win=True)
                            await manager.send_judgment_to_all(correct_guess, room_name)
                        else:
                            correct_guess = "GIUDICE ha PERSO"
                            handle_scores(user_id, session_id, mode, role=role, win=False)
                            await manager.send_judgment_to_all(correct_guess, room_name)


                else:
                    print(f"⚠️ Messaggio sconosciuto: {msg_type}") 

            except json.JSONDecodeError:
                await handle_raw_text(room_name, client_id, role, data, mode, session_id=session_id)

    except WebSocketDisconnect:
        manager.disconnect(room_name, client_id)
        await manager.broadcast(f"Client #{client_id} left {room_name}", room_name) '''

async def ws_entrypoint(websocket, room_name, client_id, cookie, backend, manager):
    role = websocket.query_params.get("role", "SPECTATOR").upper()
    mode = websocket.query_params.get("mode", "single").lower()

    print(f"🍪 Cookie disponibili: {websocket.cookies}")
    session_id, user_id = await setup_session(websocket, cookie, backend)
    print(f"SESSION_ID FINALE: {session_id}")

    await manager.connect(room_name, websocket, client_id, role)
    print(f"✅ Nuovo client {client_id} connesso come {role} in modalità {mode}")

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
                print(f"📥 Messaggio ricevuto: {message}")

                await handle_message(msg_type, room_name, websocket, role, message, mode, session_id, user_id, manager)

            except json.JSONDecodeError:
                await handle_raw_text(room_name, client_id, role, data, mode, session_id=session_id)

    except WebSocketDisconnect:
        manager.disconnect(room_name, client_id)
        await manager.broadcast(f"Client #{client_id} left {room_name}", room_name)
