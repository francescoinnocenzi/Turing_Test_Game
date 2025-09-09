from schemas.login import LoginRequest, LoginResponse
from schemas.session_data import SessionData
from database.connection import create_db_connection
from fastapi import HTTPException
from fastapi import Response
import bcrypt
import mariadb
from services.instances.session_backend import backend
from uuid import uuid4
from fastapi_sessions.frontends.implementations import SessionCookie, CookieParameters
import services.state as state



async def login(login_request: LoginRequest, response: Response, cookie: SessionCookie) -> LoginResponse:
    """
    Effettua il login di un utente tramite username o email e crea una sessione.

    Args
        login_request (LoginRequest): Contiene l'identificatore (username/email) e la password.
        response (Response): Oggetto FastAPI per attaccare il cookie di sessione.
        cookie (SessionCookie): Gestore dei cookie di sessione.

    Returns
        LoginResponse: Conferma dell'avvenuto login.

    Raises
        HTTPException: Se l'utente non esiste o la password è errata.
    """
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
        
        user_id = user[0]  # id
        print("Logged user_id:", user_id)
        
        session_uuid = uuid4() # Genero un UUID per la sessione, ovvero stringa univoca (cambia per ogni login)
        data = SessionData(user_id=user_id)   # session_id ancora None
        await backend.create(session_uuid, data) # è un dizionario che associa l'UUID alla SessionData

        cookie.attach_to_response(response, session_uuid) # Manda il cookie di sessione, quando l'utente effettua il login

        print("Creo sessione con UUID:", session_uuid)
        print("Dentro SessionData:", data.dict())

        return LoginResponse(status="ok")
    
    except mariadb.Error as e:
        raise HTTPException(status_code=422, detail=f"Errore durante l'esecuzione della query: {e}")
    
    finally:
        cur.close()
        conn.close()