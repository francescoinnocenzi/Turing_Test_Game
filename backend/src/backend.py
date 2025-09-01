from fastapi import FastAPI, Request, Depends, WebSocketDisconnect, WebSocket, HTTPException, Form, Response
from uuid import UUID

from fastapi_sessions.frontends.implementations import SessionCookie, CookieParameters
from fastapi_sessions.backends.implementations import InMemoryBackend
from fastapi_sessions.session_verifier import SessionVerifier

from schemas.question import QuestionRequest, QuestionResponse
from schemas.answer import AnswerRequest, AnswerResponse
from schemas.api_models import RequestAPI, ResponseAPI, SimilarityResponse
from schemas.judgment import JudgmentRequest, JudgmentResponse
from schemas.register import RegisterRequest, RegisterResponse
from schemas.login import LoginRequest, LoginResponse
from schemas.session_data import SessionData

from services.game.questions import create_question
from services.game.answers import create_answer
from services.auth.login import login
from services.game.judgment import create_judgment
from services.game.judgment import create_judgment
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
from schemas.session import SessionResponse, AvailableSessionsResponse
from schemas.ranking import RankingResponse

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

@app.post("/api/register", response_model=RegisterResponse)
def handle_register(register_request: RegisterRequest) -> RegisterResponse:
    return register(register_request)

@app.post("/api/login", response_model=LoginResponse)
async def handle_login(login_request: LoginRequest, response: Response) -> LoginResponse:
    return await login(login_request, response, cookie)

@app.post("/questions/create", response_model=QuestionResponse)
def generate_question(request: QuestionRequest) -> QuestionResponse:
    return create_question(request)


@app.post("/answers/create", response_model=AnswerResponse)
def generate_answer(request: AnswerRequest) -> AnswerResponse:
    return create_answer(request)

@app.post("/create/judgment", response_model=JudgmentResponse)
def handle_judgment(request: JudgmentRequest) -> JudgmentResponse:
    return create_judgment(request)

@app.websocket("/ws/{room_name}/{client_id}")
async def handle_websocket_endpoint(websocket: WebSocket, room_name: str, client_id: int) -> None:
    return await ws_entrypoint(websocket, room_name, client_id, cookie, backend, manager)

@app.post("/ask", response_model=ResponseAPI)
def handle_ask_with_memory() -> ResponseAPI:
    return ask_with_memory()

@app.post("/question/llm", response_model=dict[str, str])
def handle_create_question_llm() -> dict[str, str]:
    return create_question_llm()

@app.post("/trova_simile", response_model=SimilarityResponse)
async def handle_trova_simile(request: QuestionRequest) -> SimilarityResponse:
    return await trova_simile(request)

@app.post("/create/session", response_model=SessionResponse)
async def handle_create_session(response: Response, request: Request, session_uuid: UUID = Depends(cookie)) -> SessionResponse:
    print("session_uuid ricevuto:", session_uuid)
    return await create_session(response, request, backend, session_uuid)

@app.post("/join/session/{room_name}", response_model=SessionResponse)
async def handle_join_session(room_name: str, session_uuid: UUID = Depends(cookie)) -> SessionResponse:
    return await join_session(room_name, backend, session_uuid)

@app.get("/available/sessions", response_model=AvailableSessionsResponse)
async def handle_available_sessions() -> AvailableSessionsResponse:
    return await available_sessions()

@app.get("/ranking", response_model=RankingResponse)
def handle_ranking() -> RankingResponse:
    return get_ranking()
