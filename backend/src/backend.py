from fastapi import FastAPI, Request, WebSocketDisconnect, WebSocket, HTTPException, Form
from typing import List
import requests, json

from websocket import ConnectionManager
from database.connection import create_db_connection
from schemas.question import QuestionRequest, QuestionResponse
from schemas.answer import AnswerRequest, AnswerResponse
from schemas.session import SessionRequest, SessionResponse, SessionDetailsResponse
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

# Endpoint WebSocket per gestire la comunicazione in tempo reale
@app.websocket("/ws/{room_name}/{client_id}")
async def websocket_endpoint(websocket: WebSocket, room_name: str, client_id: int):
    # Accetta la connessione del nuovo client
    await manager.connect(room_name, websocket, client_id)
    
    try:
        # Ciclo continuo per ricevere e gestire i messaggi WebSocket
        while True:
            # Riceve un messaggio di testo dal client
            data = await websocket.receive_text()

            ws = manager.rooms[room_name][client_id]
            role = ws["role"]
            
            try:
                print(f"🔍 Parsing JSON: {data}")
                message = json.loads(data)
                message_type = message.get("type")
                text = message.get("text")
                print(f"📋 Message type: {message_type}, Role: {role}, Text: {text}")

                # Se è il giudice che manda un messaggio, è una domanda per i player
                if message_type == "question" and role == "JUDGE":
                    print("✅ JUDGE condition matched - processing question")

                    await manager.send_question_to_players(text, room_name)
                    print("📤 Question sent to players")

                    try: 
                        print("💾 Creating question request...")
                        question_request = QuestionRequest(
                            text=text,
                            room_name=room_name,
                            author_id=str(client_id),
                            session_id= 1
                        )
                        print("🔄 Calling create_question...")
                        saved_question = create_question(question_request)
                        print(f"✅ Question saved with ID: {saved_question.id}")

                        await websocket.send_text(json.dumps({
                            "type": "question_saved",
                            "question_id": saved_question.id
                        }))
                        print("📨 Confirmation sent to judge")

                    except Exception as e:
                        print(f"❌ Errore durante il salvataggio della domanda: {e}")
                
                elif message_type=="answer":
                    print("🎮 PLAYER ANSWER: Processing player response")
                    # Se è un player che risponde, manda la risposta al giudice
                    question_id = message.get("question_id")
                    print(f"🔍 Question ID from message: {question_id}")
                    player_number = 1 if role == "HUMAN" else 2  # HUMAN = Player 1, BOT = Player 2
                    await manager.send_answer_to_judge(text, room_name, player_number)
                    print("📤 Answer sent to judge")

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
                                print(f"🔍 Found question_id from database: {question_id}")
                            else:
                                print("❌ No question found for this room")
                                continue  # Salta il salvataggio se non c'è domanda
                        
                        print(f"💾 Creating answer with question_id: {question_id}")
                        answer_request = AnswerRequest(
                            question_id=question_id,
                            session_id=1,
                            text=text,
                            author_id=str(client_id),
                            author_type= ("HUMAN" if player_number == 1 else "BOT"),
                            room_name=room_name 
                        )
                        saved_answer = create_answer(answer_request)
                        print(f"✅ Answer saved with ID: {saved_answer.id}")
                        
                        # 🎯 CONTROLLA SE TUTTI HANNO RISPOSTO
                        conn = create_db_connection()
                        cursor = conn.cursor()
                        
                        # Conta le risposte per questa domanda
                        cursor.execute("""
                            SELECT COUNT(DISTINCT author_type) as unique_answers
                            FROM answers 
                            WHERE question_id = ?
                        """, (question_id,))
                        
                        answer_count = cursor.fetchone()[0]
                        cursor.close()
                        conn.close()
                        
                        print(f"📊 Risposte ricevute: {answer_count}/2")
                        
                        # Se abbiamo 2 risposte (HUMAN + BOT), tutti hanno risposto
                        if answer_count >= 2:
                            print("🎉 Tutti i player hanno risposto!")
                            # Notifica il giudice che può continuare
                            await manager.send_to_judge({
                                "type": "all_answered",
                                "message": "✅ Tutti hanno risposto! Puoi inviare la prossima domanda."
                            }, room_name)
                        
                    except Exception as e:
                        print(f"❌ Errore salvataggio risposta: {e}")
            
            except json.JSONDecodeError:
                # Se non è JSON, trattalo come testo semplice (backward compatibility)
                print(f"📨 Ricevuto testo semplice: {data} da {role}")
                if role == "JUDGE":
                    print("🎯 JUDGE: Invio domanda ai player")
                    await manager.send_question_to_players(data, room_name)
                    
                    try:
                        question_request = QuestionRequest(
                            text=data,
                            room_name=room_name,
                            author_id=str(client_id),
                            session_id=1
                        )
                        print('ciao salva')
                        saved_question = create_question(question_request)
                        print(f"✅ Domanda salvata con ID: {saved_question.id}")
                    except Exception as e:
                        print(f"❌ Errore salvataggio domanda: {e}")
                else:
                    print("🎮 PLAYER: Invio risposta al giudice")
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
                            print(f"✅ Risposta salvata per question_id: {last_question[0]}")
                        else:
                            print("❌ Nessuna domanda trovata per questa room")
                            
                    except Exception as e:
                        print(f"❌ Errore salvataggio risposta: {e}")
    except WebSocketDisconnect:
        # Gestisce la disconnessione del client
        manager.disconnect(room_name, client_id)
        # Notifica a tutti i client che il client si è disconnesso
        await manager.broadcast(f"Client #{client_id} left the {room_name}", room_name)
