from fastapi import FastAPI, Request, Depends, WebSocketDisconnect, WebSocket, HTTPException, Form, Response
from uuid import UUID

from fastapi_sessions.frontends.implementations import SessionCookie, CookieParameters
from fastapi_sessions.backends.implementations import InMemoryBackend
from fastapi_sessions.session_verifier import SessionVerifier

from schemas.question import QuestionRequest, QuestionResponse
from schemas.answer import AnswerRequest, AnswerResponse
from schemas.api_models import RequestAPI, ResponseAPI
from schemas.judgment import JudgmentRequest, JudgmentResponse
from schemas.register import RegisterRequest, RegisterResponse
from schemas.login import LoginRequest, LoginResponse
from schemas.session_data import SessionData

from services.game.questions import create_question
from services.game.answers import create_answer
from services.auth.login import login
from services.game.judgment import submit_judgment
from services.auth.register import register
from services.websocket.ws_entrypoint import ws_entrypoint
from services.llm.generate_answer import trova_simile
from services.llm.generate_question import create_question_llm
from services.llm.generate_answer import ask_with_memory
from services.game.session import create_session, join_session, available_sessions
from services.game.ranking import get_ranking
from services.instances.session_backend import backend
from services.instances.cookie import cookie
from services.instances.manager import manager

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

# 🔹 2. Configura backend e cookie
#backend = InMemoryBackend[UUID, SessionData]()# è un dizionario che mappa: una chiave (UUID) ad un valore SessionData.
# {
#   UUID("123e4567..."): SessionData(session_id=1)
# }


@app.post("/api/register")
def handle_register(register_request: RegisterRequest):
    return register(register_request)

@app.post("/api/login")
async def handle_login(login_request: LoginRequest, response: Response):
    return await login(login_request, response, cookie)

@app.post("/questions/create", response_model=QuestionResponse)
def generate_question(request: QuestionRequest):
    return create_question(request)


@app.post("/answers/create", response_model=AnswerResponse)
def generate_answer(request: AnswerRequest):
    return create_answer(request)

@app.post("/create/judgment", response_model=JudgmentResponse)
def handle_judgment(request: JudgmentRequest):
    return submit_judgment(request)
    
# Endpoint WebSocket per gestire la comunicazione in tempo reale
@app.websocket("/ws/{room_name}/{client_id}")
async def handle_websocket_endpoint(websocket: WebSocket, room_name: str, client_id: int):
    return await ws_entrypoint(websocket, room_name, client_id, cookie, backend, manager)

@app.post("/ask")
def handle_ask_with_memory():
    return ask_with_memory()

@app.post("/question/llm")
def handle_create_question_llm():
    return create_question_llm()

@app.post("/trova_simile")
async def handle_trova_simile(request: QuestionRequest):
    return await trova_simile(request)

@app.post("/create/session")
async def handle_create_session(response: Response, session_uuid: UUID = Depends(cookie)):
    print("➡️ Sono entrato in handle_create_session")
    print("📌 session_uuid ricevuto:", session_uuid)
    return await create_session(response, backend, session_uuid)

@app.post("/join/session/{room_name}")
async def handle_join_session(room_name: str, session_uuid: UUID = Depends(cookie)):
    return await join_session(room_name, backend, session_uuid)

@app.get("/available/sessions")
async def handle_available_sessions():
    return await available_sessions()

@app.get("/ranking")
def handle_ranking():
    return get_ranking()

        
for route in app.routes:
    if hasattr(route, "methods"):
        methods = ",".join(route.methods or [])
    else:
        methods = "WEBSOCKET"
    print(f"{methods:10s} -> {route.path}")