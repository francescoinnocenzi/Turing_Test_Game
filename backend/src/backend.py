from fastapi import FastAPI, Request, Depends, WebSocketDisconnect, WebSocket, HTTPException, Form, Response
from typing import List
import requests, json
from pydantic import BaseModel
import random
from uuid import uuid4, UUID
import bcrypt


from fastapi_sessions.frontends.implementations import SessionCookie, CookieParameters
from fastapi_sessions.backends.implementations import InMemoryBackend
from fastapi_sessions.session_verifier import SessionVerifier


from websocket import ConnectionManager
from database.connection import create_db_connection
from schemas.question import QuestionRequest, QuestionResponse
from schemas.answer import AnswerRequest, AnswerResponse
from schemas.api_models import RequestAPI, ResponseAPI
from schemas.judgment import JudgmentRequest, JudgmentResponse
from schemas.register import RegisterRequest, RegisterResponse
from schemas.login import LoginRequest, LoginResponse
from utils.emoji import remove_emoji

import mariadb
from pydantic import BaseModel

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Il middleware CORS serve a permettere al frontend (che gira su http://localhost:8001) 
# di parlare con il backend (che gira su http://localhost:8003).
app.add_middleware(
    CORSMiddleware,  

    # Lista di domini da cui accetto richieste
    # In questo caso solo il frontend che gira su localhost:8001
    allow_origins=["http://localhost:8001"],  

    # Permette l'invio dei cookie e credenziali (es. Authorization header)
    # Necessario se usi SessionCookie o fetch con credentials: "include"
    allow_credentials=True,  

    # Quali metodi HTTP permettere (GET, POST, PUT, DELETE...)
    # Con "*" vuol dire tutti i metodi
    allow_methods=["*"],  

    # Quali header permettere nella richiesta
    # Con "*" vuol dire tutti i possibili header
    allow_headers=["*"],  
)

# Crea un'istanza del gestore connessioni
manager = ConnectionManager()

# 🔹 1. Definisci SessionData
class SessionData(BaseModel):
    user_id: int # id user_logato
    session_id: int | None = None

# 🔹 2. Configura backend e cookie
backend = InMemoryBackend[UUID, SessionData]()# è un dizionario che mappa: una chiave (UUID) ad un valore SessionData.
# {
#   UUID("123e4567..."): SessionData(session_id=1)
# }

cookie_params = CookieParameters(
    # max_age=3600,        # durata cookie 1h
    # path="/",
    # same_site="none",    # 👈 necessario per cross-origin
    # secure=False         # 👈 localhost usa http, non https
)

cookie = SessionCookie(
    cookie_name="session",
    identifier="general_verifier",
    auto_error=False,
    secret_key="your-secret-key-change-this",  # cambia con una chiave sicura!
    cookie_params=cookie_params,
)

@app.post("/api/register")
def register(register_request: RegisterRequest):
    conn = create_db_connection()
    cur = conn.cursor()

    username = register_request.username
    email = register_request.email
    password = register_request.password

    try:
        password = register_request.password.encode("utf-8")
        hashed = bcrypt.hashpw(password, bcrypt.gensalt())

        cur.execute("INSERT INTO users (username, password_hash, email) VALUES (%s, %s, %s)",(username, hashed.decode("utf-8"), email))

        conn.commit()

        return RegisterResponse(status="ok")

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=422, detail=f"Errore durante l'inserimento: {e}")

    finally:
        cur.close()
        conn.close()

@app.post("/api/login")
async def login(login_request: LoginRequest, response: Response):
    conn = create_db_connection()
    cur = conn.cursor()

    identifier = login_request.identifier
    password = login_request.password

    try:
       # Cerco sia per username che per email
        cur.execute("SELECT id, username, password_hash, email FROM users WHERE username = %s OR email = %s", (identifier, identifier))
        user = cur.fetchone()

        if user is None:
            raise HTTPException(status_code=401, detail="Utente non trovato")
        
        stored_password = user[2]  # password hash
        if not bcrypt.checkpw(password.encode("utf-8"), stored_password.encode("utf-8")):
            raise HTTPException(status_code=401, detail="Password errata")    
        
        global user_id
        user_id = user[0]  # id
        print("Logged user_id:", user_id)
        
        session_uuid = uuid4()
        data = SessionData(user_id=user_id)   # session_id ancora None
        await backend.create(session_uuid, data)

        cookie.attach_to_response(response, session_uuid)

        print("👉 Creo sessione con UUID:", session_uuid)
        print("👉 Dentro SessionData:", data.dict())


        return LoginResponse(status="ok")
    
    except mariadb.Error as e:
        raise HTTPException(status_code=422, detail=f"Errore durante l'esecuzione della query: {e}")
    
    finally:
        cur.close()
        conn.close()

@app.post("/questions/create", response_model=QuestionResponse)
def create_question(request: QuestionRequest):
    conn = create_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO questions (session_id, text, author_user_id, author_type, room_name) 
            VALUES (?, ?, ?, ?, ?)
        """, (request.session_id, request.text, request.author_user_id, request.author_type, request.room_name,))
        conn.commit()

        question_id = cursor.lastrowid

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

@app.post("/answers/create", response_model=AnswerResponse)
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

@app.post("/create/judgment", response_model=JudgmentResponse)
def submit_judgment(request: JudgmentRequest):
    conn = create_db_connection()
    cursor = conn.cursor()

    try:
        # Salva il giudizio
        cursor.execute("""
            INSERT INTO judgments (session_id, judge_id, chosen_player_human)
            VALUES (?, ?, ?)
        """, (request.session_id, request.judge_id, request.chosen_player_human, ))
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

async def check_and_finalize_game(session_id: int, room_name: str, question_count: int, max_questions: int, role: str, mode: str):
    """
    Controlla se il numero massimo di domande è stato raggiunto
    e in caso affermativo esegue il giudizio finale e chiude la partita.
    """
    if question_count >= max_questions:

        if mode == "single" and role == "HUMAN":
            # Fine partita - esegui giudizio
            judgment_result = await get_llm_judgment(session_id)
            # Invia risultato finale
        
            print(f"GIUDIZIO {judgment_result}")
            
            if "judgment" in judgment_result:
                # Invia il giudizio a tutti i client
                await manager.send_judgment_to_all(judgment_result["human_result"], room_name)
                print(f"Giudizio inviato: {judgment_result['human_result']}")
            else:
                print(f"Errore nel giudizio: {judgment_result.get('error', 'Errore sconosciuto')}")
        
        if mode == "single" and role == "JUDGE":
            await manager.send_message_to_all("Scegli chi è UMANO", "time_to_judge", room_name)


    
async def check_all_answered(question_id: int, room_name: str, session_id: int, role: str, mode: str):
    """Verifica se tutti i player hanno risposto alla domanda"""
    try:
        conn = create_db_connection()
        cursor = conn.cursor()

        # Conta domande per questa sessione
        cursor.execute("""
            SELECT COUNT(*) FROM questions 
            WHERE session_id = ?
        """, (session_id,))

        question_count = cursor.fetchone()[0]
        MAX_QUESTIONS = 2  # Configurabile

        await check_and_finalize_game(session_id, room_name, question_count, MAX_QUESTIONS, role, mode)
        
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
            print("✅ Tutti hanno risposto!")
            await manager.send_to_judge({ 
                "type": "all_answered", 
                "message": "✅ Tutti hanno risposto! Puoi inviare la prossima domanda." 
                }, room_name)
            
            if role == "HUMAN" and mode == "single" and question_count < MAX_QUESTIONS:
                await auto_generate_next_question(room_name, session_id)
            
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

                if msg_type == "question": #Gestione della domanda in arrivo
                    await handle_question(room_name, client_id, websocket, role, message, mode, session_id, user_id)

                elif msg_type == "answer": #Gestione della riposta in arrivo
                    await handle_answer(room_name, client_id, websocket, role, message, mode, session_id, user_id)
                
                elif msg_type == "judge_choice":
                    chosen_player_human = message.get("chosen_player_human")

                    judgment_req = JudgmentRequest(
                        session_id=session_id,
                        judge_id=1234,
                        chosen_player_human=chosen_player_human
                    )

                    result_judgment = submit_judgment(judgment_req)
                    judge_choice = result_judgment.chosen_player_human
                    
                    player_a_real_type = "HUMAN"
                    player_b_real_type = "BOT"

                    correct_answer = False

                    if judge_choice == 'A' and player_a_real_type == "HUMAN":
                        correct_answer = True
                    elif judge_choice == 'B' and player_b_real_type == "HUMAN":
                        correct_answer = True 

                    print(f"SCELTA FRONTEND: {judge_choice}")
                    if correct_answer:
                        correct_guess = "GIUDICE ha VINTO"
                        handle_scores(user_id, session_id,mode, win = True) #Aggiorno i punteggi nel DB
                    else: 
                        "GIUDICE ha PERSO"
                        handle_scores(user_id, session_id,mode, win= False) #Aggiorno i punteggi nel DB
                    
                    await manager.send_judgment_to_all(correct_guess, room_name)
                    

                else:
                    print(f"⚠️ Messaggio sconosciuto: {msg_type}")

            except json.JSONDecodeError:
                await handle_raw_text(room_name, client_id, role, data, mode, session_id=session_id)

    except WebSocketDisconnect:
        manager.disconnect(room_name, client_id)
        await manager.broadcast(f"Client #{client_id} left {room_name}", room_name)
#Gestione della domanda in arrivo (singleplayer)
async def handle_question(room_name, client_id, websocket, role, message, mode, session_id, user_id):
    text = message.get("text")
    print(f"❓ Domanda dal giudice {client_id}: {text}")

    # Invia ai bot
    await manager.send_question_to_players(text, room_name)

    # Salva domanda
    q_req = QuestionRequest(
        text=text,
        room_name=room_name,
        author_user_id=user_id,
        session_id=session_id,
        author_type="HUMAN"
    )
    saved_q = create_question(q_req)

    await websocket.send_text(json.dumps({
        "type": "question_saved",
        "question_id": saved_q.id
    }))

    # BOT 1 (LLM)
    bot1_resp = await get_llm_response(text)
    #Salva risposta bot 
    create_answer(AnswerRequest(
        question_id=saved_q.id,
        session_id=session_id,
        text=bot1_resp,
        author_user_id=None,
        author_type="BOT",
        room_name=room_name
    ))
    await manager.send_answer_to_judge(bot1_resp, room_name, 2)
    print(f"🤖 BOT-LLM answer sent: {bot1_resp}")  # <-- log
    
    # BOT 2 (retrieval o fallback LLM)
    bot2_data = await trova_simile(q_req)
    bot2_resp = bot2_data["risposta_trovata"]
    
    #Salva risposta bot retrival solo se generata da LLM (perche HUMAN è gia presente nel DB)

    create_answer(AnswerRequest(
        question_id=saved_q.id,
        session_id=session_id,
        text=bot2_resp,
        author_user_id=None,
        author_type="BOT_AS_HUMAN" if bot2_data["tipo_risposta"] == "LLM" else "HUMAN",
        room_name=room_name
    ))
    await manager.send_answer_to_judge(bot2_resp, room_name, 1) #metto 1 perche risponde al posto di HUMAN
    print(f"🤖 BOT-Retrieval answer sent: {bot2_resp}")  # <-- log

    await check_all_answered(saved_q.id, room_name, session_id=session_id, role="JUDGE", mode=mode)

#Gestione della risposta inviata singleplayer
async def handle_answer(room_name, client_id, websocket, role, message, mode, session_id, user_id):
    text = message.get("text")
    question_id = message.get("question_id")

    player_number = 1 if role == "HUMAN" else 2
    print(f"💬 Risposta da {role} (client {client_id}): {text}")

    await manager.send_answer_to_judge(text, room_name, player_number)

    if not question_id:
        conn = create_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id FROM questions 
            WHERE room_name = ? 
            ORDER BY created_at DESC 
            LIMIT 1
        """, (room_name,))
        last_q = cur.fetchone()
        cur.close(); conn.close()
        if last_q:
            question_id = last_q[0]

    if question_id:
        create_answer(AnswerRequest(
            question_id=question_id,
            session_id=session_id,
            text=text,
            author_user_id=user_id,
            author_type=role,
            room_name=room_name
        ))
    
    # Usa la funzione centralizzata per verificare se tutti hanno risposto
    await check_all_answered(question_id, room_name, session_id=session_id, role=role, mode=mode)
    
#Gestione caso domanda automatica in singleplayer
async def process_auto_question(room_name, websocket, question, session_id):
    #Ivia domanda ai player (Uno è il giocatore l'altro è il bot)
    await manager.send_question_to_players(question, room_name)

    q_req = QuestionRequest(
        text=question,
        room_name=room_name,
        author_user_id=None,
        author_type="BOT",
        session_id=session_id
    )
    saved_q = create_question(q_req)

    await websocket.send_text(json.dumps({
        "type": "question_saved",
        "question_id": saved_q.id
    }))

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
    await manager.send_answer_to_judge(bot_resp, room_name, 2)
    print(f"🤖 BOT-AUTO answer sent: {bot_resp}")
    

async def handle_raw_text(room_name, client_id, role, text, mode, session_id):
    print(f"📥 Raw text da {role}: {text}")
    # if role == "JUDGE":
    #     await handle_question(room_name, client_id, role, {"text": text}, None, mode, session_id=session_id)
    # else:
    #     await handle_answer(room_name, client_id, role, {"text": text}, None, mode, session_id=session_id)

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


previous_questions : list[str] = []

@app.post("/question/llm")
def create_question_llm():

    url = "http://ollama:11434/api/chat"

    themes = ["cultura", "calcio", "sport", "cucina", "moda", "abitudini", "emozioni", "passioni"]
    theme = random.choice(themes)

    question_prompt = {
        "role": "system",
        "content": (
            "Crea una sola domanda breve (max 7 parole). "
            "Naturale e colloquiale, stile chat. "
            "Solo la domanda, niente emoji. "
            "Evita riferimenti a personaggi famosi, politica o attualità. "
            "Tema: {theme}. "
            "Non ripetere domande già fatte."
        )
    }

    messages = [
        question_prompt,
        {"role": "user", "content": f"Genera una domanda sul tema: {theme}"}
    ]


    global previous_questions

    for question in previous_questions:
        messages.append({
            "role": "user",
            "content": f"Domanda già fatta: {question}"
        })

    print(messages)

    payload = {
        "model": "gemma2:2b-instruct-q2_K",
        "messages": messages,
        "stream": False
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        risposta_api = response.json()
        
        # print("Payload inviato a Ollama:\n", json.dumps(payload, indent=2))

        question = risposta_api["message"]["content"]
        previous_questions.append(question)

        return {"question": question} 
           
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Errore durante richiesta post {e}")

# ...existing code...

async def get_llm_judgment(session_id: int):
    """Fa decidere all'LLM chi è HUMAN e chi è BOT basandosi sulle risposte della sessione"""
    try:
        # Recupera tutte le domande e risposte per questa sessione
        conn = create_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT q.text as question, a.text as answer, a.author_type, a.author_user_id
            FROM questions q
            JOIN answers a ON q.id = a.question_id
            WHERE q.session_id = ? AND a.session_id = ?
            ORDER BY q.created_at, a.author_type
        """, (session_id, session_id))
        
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if not results:
            return {"error": f"Nessuna risposta trovata per la sessione {session_id}"}
        
        # Organizza le risposte per player
        human_responses = []
        bot_responses = []
        
        for row in results:
            question, answer, author_type, author_user_id = row
            
            if author_type == "HUMAN":
                human_responses.append(f"Q: {question}\nA: {answer}")
            elif author_type == "BOT":
                bot_responses.append(f"Q: {question}\nA: {answer}")
        
        # Randomizza SOLO i nomi, non i dati
        import random
        player_a_name = "Player A"
        player_b_name = "Player B"

        players_data = [
            (human_responses, "HUMAN"),
            (bot_responses, "BOT")  
        ]
        random.shuffle(players_data)
        
        # Ora assegna in modo chiaro
        player_a_responses, player_a_real_type = players_data[0]
        player_b_responses, player_b_real_type = players_data[1]
        
        # Prepara il prompt per l'LLM giudice
        judgment_prompt = {
            "role": "system",
            "content": (
                "Sei un giudice in un Turing Test. "
                "Analizza le risposte dei due player e decidi chi è UMANO e chi è IA/BOT. "
                "Concentrati su: naturalezza, errori umani, stile di scrittura, coerenza. "
                "Gli umani spesso fanno errori di battitura, sono meno precisi, più colloquiali. "
                "Le IA sono spesso più precise, formali, evitano errori. "
                "Rispondi SOLO con: 'Player A è UMANO' oppure 'Player B è UMANO'."
            )
        }
        
        conversation_data = {
            "role": "user", 
            "content": (
                f"{player_a_name} (risposte):\n" + "\n\n".join(player_a_responses) + 
                "\n\n--- SEPARATORE ---\n\n" +
                f"{player_b_name}(risposte):\n" + "\n\n".join(player_b_responses) +
                "\n\n Rispondi SOLO con 'Player A è UMANO' o 'Player B è UMANO'."
            )
        }

        print(conversation_data)

        messages = [judgment_prompt, conversation_data]
        
        # Chiama l'LLM per il giudizio
        url = "http://ollama:11434/api/chat"
        payload = {
            "model": "gemma2:2b-instruct-q2_K",
            "messages": messages,
            "stream": False
        }
        
        response = requests.post(url, json=payload)
        response.raise_for_status()
        risposta_api = response.json()
        
        llm_judgment = risposta_api["message"]["content"].strip()

        llm_choice = None

        if "Player A è UMANO" in llm_judgment:
            llm_choice = 'A'
        elif "Player B è UMANO" in llm_judgment:
            llm_choice = 'B'

        print(player_b_real_type, player_a_real_type)
        
        # All' inizio imposto variabile su falso, se non ha indovinato LLM rimane falso, altrimenti cambia valore in vero
        correct_answer = False

        if llm_choice == 'A' and player_a_real_type == "HUMAN":
            correct_answer = True
        elif llm_choice == 'B' and player_b_real_type == "HUMAN":
            correct_answer = True
        
        return {
            "correct_answer": correct_answer,
            "llm_choice": llm_choice,
            "judgment": llm_judgment,
            "session_id": session_id,
            "human_responses": len(human_responses),
            "bot_responses": len(bot_responses),
            "correct_guess": ("GIUDICE ha VINTO" if correct_answer else "GIUDICE ha PERSO"),
            "human_result": ("HUMAN ha VINTO" if not correct_answer else "HUMAN ha PERSO")
        }
        
    except Exception as e:
        print(f"Errore nel giudizio LLM: {e}")
        return {"error": str(e)}

# def check_judge_choice(session_id: int, judge_choice: str):



from sentence_transformers import SentenceTransformer, util
import torch

model = None

def get_model():
    global model
    if model is None:
        model = SentenceTransformer("nickprock/sentence-bert-base-italian-uncased")
    return model

@app.post("/trova_simile")
async def trova_simile(request: QuestionRequest):
    
    # In questo modo il backend parte subito, e il modello viene caricato solo alla prima chiamata API.
    model = get_model()

    #Connessione al database per prendere domande 
    conn = create_db_connection()
    cursor = conn.cursor()

    input_frase = request.text #domada inserita in input
    soglia_similarità = 0.8
    try:
        cursor.execute("""
            SELECT id,text
            FROM questions
            WHERE session_id != ?
            """, (request.session_id,)
        )
        #lista di coppie trovate (id,question)
        frasi_trovate = cursor.fetchall() # [(1,"ciao"),(2,"prova")...]
        print(input_frase,frasi_trovate)
        if not frasi_trovate:
            #se non trovo domande precedenti allora creo risposta  nuova con LLM
            risposta_nuova = await get_llm_response(input_frase)

            return {
                "frase_input": input_frase,
                "frase_simile": None,
                "risposta_trovata": risposta_nuova,
                "similarità": 0.0,
                "tipo_risposta" : "LLM"
            }
        #lista di sole question trovate
        frasi_db = [row[1] for row in frasi_trovate]

        # Embedding della frase in ingresso
        embedding_input = model.encode(input_frase, convert_to_tensor=True)
        # Embeddings frasi da DB
        embeddings_db = model.encode(frasi_db, convert_to_tensor=True)

        # Calcolo similarità coseno sulle frasi input e database
        cosine_scores = util.cos_sim(embedding_input, embeddings_db)

        # Trovo indice della frase più simile
        best_idx = cosine_scores.argmax().item() #indice frase piu siile
        best_score = cosine_scores[0][best_idx].item() #score frase piu simile
        best_sentence = frasi_db[best_idx] #frase piu simile
        best_id = frasi_trovate[best_idx][0] # id frase piu simile
        #cerco una risposta possibile della domanda piu simile

        cursor.execute("""
            SELECT id,text
            FROM answers
            WHERE question_id = ? and author_type = 'HUMAN'
            ORDER BY RAND()
            LIMIT 1
            """, (best_id,)
        )
        #coppia (id, risposta) casuale trovata
        coppia_trovata = cursor.fetchone() # 
        risposta_trovata = coppia_trovata[1] if coppia_trovata else None; #nel caso non trova nulla da None
    except mariadb.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()
    print(f"BEST SCORE {best_score}")

    if best_score > soglia_similarità and risposta_trovata is not None:
        return {
            "frase_input": input_frase,
            "frase_simile": best_sentence,
            "risposta_trovata": risposta_trovata,
            "similarità": best_score,
            "tipo_risposta" : "HUMAN"
        }
    else:
        risposta_nuova = await get_llm_response(input_frase)

        return {
            "frase_input": input_frase,
            "frase_simile": None,
            "risposta_trovata": risposta_nuova,
            "similarità": 0.0,
            "tipo_risposta" : "LLM"
        }
    
@app.post("/create/session")
async def create_session(response: Response, session_uuid: UUID = Depends(cookie)):
    conn = create_db_connection()
    cursor = conn.cursor()

    try:
        # 1. Salvo nel DB
        cursor.execute("INSERT INTO sessions (room_name) VALUES ('room1');")
        conn.commit()
        db_session_id = cursor.lastrowid

        print("👉 Richiesta arrivata a /create/session")
        print("👉 session_uuid letto dal cookie:", session_uuid)

        # recupero dati attuali (con user_id già dentro)
        old_data = await backend.read(session_uuid)
        print("👉 Dati vecchi dal backend:", old_data)

        if not old_data:
            raise HTTPException(status_code=404, detail="Session not found")

        # aggiorno solo session_id, user_id rimane intatto
        updated = old_data.model_copy(update={"session_id": db_session_id})
        await backend.update(session_uuid, updated)

        print("User ID:", updated.user_id)
        print("Session ID:", updated.session_id)

        return {
            "status": "Success",
            "db_session_id": db_session_id,
            "session_uuid": str(session_uuid),
        }

    except mariadb.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cursor.close()
        conn.close()

async def auto_generate_next_question(room_name: str, session_id: int):
    """Genera automaticamente la prossima domanda dopo che tutti hanno risposto"""
    try:
        import asyncio
        
        # Piccolo delay per dare tempo all'utente di leggere le risposte
        await asyncio.sleep(5)
        
        # Genera nuova domanda
        print("🎯 Auto-generando prossima domanda...")
        next_question = await get_llm_question()
        
        if next_question:
            print(f"📝 Nuova domanda: {next_question}")
            
            # Invia la domanda ai player
            await manager.send_question_to_players(next_question, room_name)
            
            # Salva nel database
            question_request = QuestionRequest(
                text=next_question,
                room_name=room_name,
                author_user_id=None,
                session_id=session_id,
                author_type="BOT"
            )
            saved_question = create_question(question_request)
            
            print(f"✅ Domanda salvata con ID: {saved_question.id}")
            
            # Genera risposta automatica del bot
            print("🤖 Generando risposta automatica del bot...")
            bot_response = await get_llm_response(next_question)
            
            # Salva la risposta del bot
            bot_answer_request = AnswerRequest(
                question_id=saved_question.id,
                session_id=session_id,
                text=bot_response,
                author_user_id=None,
                author_type="BOT",
                room_name=room_name
            )
            create_answer(bot_answer_request)
            
            print(f"🤖 Risposta bot salvata: {bot_response}")

            # await manager.send_message_to_all("Puoi rispondere alla nuova domanda!", "question_new", room_name)

            return next_question
            
        else:
            print("❌ Errore nella generazione della domanda automatica")

            return None
            
    except Exception as e:
        print(f"❌ Errore in auto_generate_next_question: {e}")


def handle_scores(user_id: int, session_id: int, mode: str, win: bool):
    """Aggiorna i punteggi dei giocatori in base al risultato della partita"""
    conn = create_db_connection()
    cursor = conn.cursor()

    try:
        if mode== "single":
            score = 1 if win else 0
            cursor.execute("""
                INSERT INTO scores (user_id, session_id, score, mode)
                VALUES (?, ?, ?, ?)
            """, (user_id, session_id, score, "SINGLEPLAYER"))
        else:
            raise Exception("Modalità non supportata per il calcolo punteggi")

        conn.commit()

    except Exception as e:
        conn.rollback()
        print(f"Errore nell'aggiornamento punteggi: {e}")
    finally:
        cursor.close()
        conn.close()
        