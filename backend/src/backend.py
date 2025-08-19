from fastapi import FastAPI, Request, WebSocketDisconnect, WebSocket, HTTPException, Form
from typing import List
import requests, json
from pydantic import BaseModel
import random


from websocket import ConnectionManager
from database.connection import create_db_connection
from schemas.question import QuestionRequest, QuestionResponse
from schemas.answer import AnswerRequest, AnswerResponse
from schemas.api_models import RequestAPI, ResponseAPI
from utils.emoji import remove_emoji

import mariadb
from pydantic import BaseModel

app = FastAPI()

# Crea un'istanza del gestore connessioni
manager = ConnectionManager()


@app.post("/questions/create", response_model=QuestionResponse)
def create_question(request: QuestionRequest):
    conn = create_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO questions (session_id, text, author_id, room_name) 
            VALUES (?, ?, ?, ?)
        """, (request.session_id, request.text, request.author_id, request.room_name,))
        conn.commit()

        question_id = cursor.lastrowid

        cursor.execute("""
            SELECT id, session_id, text, author_id, room_name, created_at
            FROM questions
            WHERE id = ?
        """, (question_id,))
        row = cursor.fetchone()

        return QuestionResponse(
            id=row[0], 
            session_id=row[1], 
            text=row[2],
            author_id=row[3], 
            room_name=row[4], 
            created_at=row[5]
        )

    except mariadb.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.post("/answers/create", response_model=AnswerResponse)
def create_answer(request: AnswerRequest):
    conn = create_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO answers (question_id, session_id, text, author_id, author_type, room_name) 
            values (?, ?, ?, ?, ?, ?)
        """, (request.question_id, request.session_id, request.text, request.author_id, request.author_type, request.room_name))
        conn.commit()

        answer_id = cursor.lastrowid

        cursor.execute("""
            SELECT id, question_id, session_id, text, author_id, author_type, room_name, created_at
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
            author_id=row[4],
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

# Funzione per verificare se tutti hanno risposto e inviare notifica
# ...existing code...

async def check_all_answered(question_id: int, room_name: str):
    """Verifica se tutti i player hanno risposto alla domanda"""
    try:
        conn = create_db_connection()
        cursor = conn.cursor()
        
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
            print("✅ Tutti hanno risposto! Inviando giudizio LLM...")
            
            # Richiedi il giudizio dell'LLM
            judgment_result = await get_llm_judgment(session_id=1)

            print(f"GIUDIZIO {judgment_result}")
            
            if "judgment" in judgment_result:
                # Invia il giudizio a tutti i client
                await manager.send_judgment_to_all(judgment_result["judgment"], room_name)
                print(f"Giudizio inviato: {judgment_result['judgment']}")
            else:
                print(f"Errore nel giudizio: {judgment_result.get('error', 'Errore sconosciuto')}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Errore in check_all_answered: {e}")

# Funzione per ottenere risposta dal LLM
async def get_llm_response(question: str):
    """Funzione che chiama l'API LLM per ottenere una risposta alla domanda"""
    request_data = RequestAPI(question=question)
    try:
        response = chat_with_memory(request_data)
        return response.answer
    except Exception as e:
        print(f"❌ Errore nella chiamata a LLM: {e}")
        return "Mi dispiace, non ho capito la domanda."

# Funzione per ottenere domanda dal LLM
async def get_llm_question():
    """Funzione che chiama l'API LLM per ottenere una domanda"""
    try:
        response = create_question_llm()
        print(f"RESPONSE {response}")
        return response.get("question")
    except Exception as e:
        print(f"❌ Errore nella chiamata a LLM: {e}")
        return "Errore nella generazione domanda."
    
# Endpoint WebSocket per gestire la comunicazione in tempo reale
@app.websocket("/ws/{room_name}/{client_id}")
async def websocket_endpoint(websocket: WebSocket, room_name: str, client_id: int):

    role = websocket.query_params.get("role", "SPECTATOR").upper()
    mode = websocket.query_params.get("mode", "multi").lower()

    print(role, mode)

    # Accetta la connessione del nuovo client
    await manager.connect(room_name, websocket, client_id, role)

    if role == "HUMAN" and mode == "single":
        room_clients = manager.rooms.get(room_name, {})
        roles = [ws["role"] for ws in room_clients.values()]

        if "JUDGE" not in roles:                        
            question = await get_llm_question()

            print(f"DOMANDA LLM: {question}")

            if question:
                # Invia la domanda subito all'HUMAN
                await manager.send_question_to_players(question, room_name)
            
                try:
                    question_request = QuestionRequest(
                        text=question,
                        room_name=room_name,
                        author_id="system-auto",
                        session_id=1
                    )
                    saved_question = create_question(question_request)

                    await websocket.send_text(json.dumps({
                        "type": "question_saved",
                        "question_id": saved_question.id
                    }))
                    print("Confirmation sent to judge")

                    # Ottieni risposta automatica dal bot LLM
                    print("🤖 Richiedendo risposta automatica al bot...")
                    bot_response = await get_llm_response(question)
                    print(f"🤖 Risposta bot: {bot_response}")

                    # Salva la risposta del bot
                    bot_answer_request = AnswerRequest(
                        question_id=saved_question.id,
                        session_id=1,
                        text=bot_response,
                        author_id="bot-auto",
                        author_type="BOT",
                        room_name=room_name
                    )
                    saved_bot_answer = create_answer(bot_answer_request)
                    print(f"Bot answer saved with ID: {saved_bot_answer.id}")
                
                except Exception as e:
                    print(f"Errore durante il processo: {e}")
    
    try:
        # Ciclo continuo per ricevere e gestire i messaggi WebSocket
        while True:
            # Riceve un messaggio di testo dal client
            data = await websocket.receive_text()

            ws = manager.rooms[room_name][client_id]
            role = ws["role"]
            
            try:
                message = json.loads(data)
                message_type = message.get("type") 
                text = message.get("text")
                print(f"Message type: {message_type}, Role: {role}, Text: {text}")

                # Se è il giudice che manda un messaggio, è una domanda per i player
                if message_type == "question":
                    print("JUDGE condition matched - processing question")

                    await manager.send_question_to_players(text, room_name)
                    print("Question sent to players")

                    try: 
                        print("Creating question request...")
                        question_request = QuestionRequest(
                            text=text,
                            room_name=room_name,
                            author_id=str(client_id),
                            session_id= 1
                        )
                        print("Calling create_question...")
                        saved_question = create_question(question_request)
                        print(f"Question saved with ID: {saved_question.id}")

                        await websocket.send_text(json.dumps({
                            "type": "question_saved",
                            "question_id": saved_question.id
                        }))
                        print("Confirmation sent to judge")
                        
                        # Ottieni risposta automatica dal bot LLM
                        print("🤖 Richiedendo risposta automatica al bot...")
                        bot_response = await get_llm_response(text)
                        print(f"🤖 Risposta bot: {bot_response}")

                        # Salva la risposta del bot
                        bot_answer_request = AnswerRequest(
                            question_id=saved_question.id,
                            session_id=1,
                            text=bot_response,
                            author_id="bot-auto",
                            author_type="BOT",
                            room_name=room_name
                        )
                        saved_bot_answer = create_answer(bot_answer_request)
                        print(f"Bot answer saved with ID: {saved_bot_answer.id}")

                        # Invia la risposta del bot al giudice
                        await manager.send_answer_to_judge(bot_response, room_name, 2)  # 2 = BOT
                        print("Bot answer sent to judge")

                        # Usa la funzione centralizzata per verificare se tutti hanno risposto
                        await check_all_answered(saved_question.id, room_name)

                    except Exception as e:
                        print(f"Errore durante il processo: {e}")
                
                elif message_type=="answer":
                    print("PLAYER ANSWER: Processing player response")
                    # Se è un player che risponde, manda la risposta al giudice
                    question_id = message.get("question_id")
                    print(f"Question ID from message: {question_id}")
                    player_number = 1 if role == "HUMAN" else 2  # HUMAN = Player 1, BOT = Player 2
                    await manager.send_answer_to_judge(text, room_name, player_number)
                    print("Answer sent to judge")

                    try:
                        # Se non c'è question_id nel messaggio, ottienilo dal database
                        if not question_id:
                            print("🔍 No question_id provided, fetching from database...")
                            conn = create_db_connection()
                            cursor = conn.cursor()
                            
                            cursor.execute("""
                                SELECT id FROM questions 
                                WHERE room_name = ? 
                                ORDER BY created_at DESC 
                                LIMIT 1
                            """, (room_name,))
                            
                            last_question = cursor.fetchone()
                            cursor.close()
                            conn.close()
                            
                            if last_question:
                                question_id = last_question[0]
                                print(f"Found question_id from database: {question_id}")
                            else:
                                print("No question found for this room")
                                continue  # Salta il salvataggio se non c'è domanda
                        
                        print(f"Creating answer with question_id: {question_id}")
                        answer_request = AnswerRequest(
                            question_id=question_id,
                            session_id=1,
                            text=text,
                            author_id=str(client_id),
                            author_type= ("HUMAN" if player_number == 1 else "BOT"),
                            room_name=room_name 
                        )
                        saved_answer = create_answer(answer_request)
                        print(f"Answer saved with ID: {saved_answer.id}")
                        
                        # Usa la funzione centralizzata per verificare se tutti hanno risposto
                        await check_all_answered(question_id, room_name)
                        
                    except Exception as e:
                        print(f"Errore salvataggio risposta: {e}")
            
            except json.JSONDecodeError:
                # Se non è JSON, trattalo come testo semplice (backward compatibility)
                print(f"Ricevuto testo semplice: {data} da {role}")
                if role == "JUDGE":
                    print("JUDGE: Invio domanda ai player")
                    await manager.send_question_to_players(data, room_name)
                    
                    try:
                        question_request = QuestionRequest(
                            text=data,
                            room_name=room_name,
                            author_id=str(client_id),
                            session_id=1
                        )

                        saved_question = create_question(question_request)
                        print(f"Domanda salvata con ID: {saved_question.id}")
                    except Exception as e:
                        print(f"Errore salvataggio domanda: {e}")
                else:
                    print("PLAYER: Invio risposta al giudice")
                    player_number = 1 if role == "HUMAN" else 2
                    await manager.send_answer_to_judge(data, room_name, player_number)
                    
                    # Salva la risposta nel database
                    try:
                        # Ottieni l'ultima domanda per questa room
                        conn = create_db_connection()
                        cursor = conn.cursor()
                        
                        cursor.execute("""
                            SELECT id FROM questions 
                            WHERE room_name = ? 
                            ORDER BY created_at DESC 
                            LIMIT 1
                        """, (room_name,))
                        
                        last_question = cursor.fetchone()
                        print(last_question)
                        cursor.close()

                        conn.close()
                        
                        if last_question:
                            answer_request = AnswerRequest(
                                question_id=last_question[0],
                                session_id=1,
                                text=data,
                                author_id=str(client_id),
                                author_type=("HUMAN" if player_number == 1 else "BOT"),
                                room_name=room_name
                            )
                            create_answer(answer_request)
                            print(f"Risposta salvata per question_id: {last_question[0]}")
                        else:
                            print("Nessuna domanda trovata per questa room")
                            
                    except Exception as e:
                        print(f"Errore salvataggio risposta: {e}")
    except WebSocketDisconnect:
        # Gestisce la disconnessione del client
        manager.disconnect(room_name, client_id)
        # Notifica a tutti i client che il client si è disconnesso
        await manager.broadcast(f"Client #{client_id} left the {room_name}", room_name)

chat_history: list[dict]= []

@app.post("/ask")
def chat_with_memory(request: RequestAPI):

    global chat_history

    chat_history.append({"role": "user", "content": request.question})

    url = "http://ollama:11434/api/chat"

    system_prompt = {
        "role": "system",
        "content": (
            "Rispondi come un essere umano. Stile naturale, diretto e realistico. Chat informale: risposte brevi, massimo  10 parole. Evita frasi inutili o generiche.  Non dire mai che sei un'IA. Se ti chiedono nome, età, luogo o famiglia, inventa risposte credibili. Non dire mai che non sai o rifiutare di rispondere."
        )
    }

    # "content": (
    #         "Rispondi come un essere umano. Usa uno stile naturale, diretto e realistico. "
    #         "Non usare emoji, simboli speciali o Markdown. "
    #         "Massimo 150 caratteri per risposta. "
    #         "Evita frasi inutili o generiche. "
    #         "Non dire mai che sei un'IA. "
    #         "Se ti chiedono il nome, età, luogo di nascita o famiglia, inventa risposte credibili. "
    #         "Non dire mai che non sai. Non rifiutare mai di rispondere."
    #     )

    # Mettendo il system prompt all'inizio, il modello LLM lo considera come una direttiva ad alta priorità che deve guidare tutte le sue risposte.
    messages: list = [system_prompt] + chat_history  # prepend il system

    payload = {
        "model": "gemma2:2b-instruct-q2_K", #Versione ottimizzata di gemma2:2b
        "messages": messages,
        "stream": False
    }

    try:

        response = requests.post(url, json=payload)
        response.raise_for_status()
        risposta_api = response.json()
        
        print("Payload inviato a Ollama:\n", json.dumps(payload, indent=2))

        answer = risposta_api["message"]["content"]
        answer = remove_emoji(answer)
        
        chat_history.append({"role": "assistant", "content": answer})

        print(chat_history)

        return ResponseAPI(answer=answer, chat_history=chat_history)
        
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Errore durante richiesta post {e}")
    