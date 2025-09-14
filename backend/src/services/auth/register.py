from schemas.register import RegisterRequest, RegisterResponse
from database.connection import create_db_connection
from fastapi import HTTPException
import bcrypt

def register(register_request: RegisterRequest) -> RegisterResponse:
    """
    Registra un nuovo utente nel database.

    Args
        register_request (RegisterRequest): Dati dell'utente da registrare

    Returns
        RegisterResponse: Conferma dell'avvenuta registrazione.
    
    Raises
        HTTPException: Se si verifica un errore durante l'inserimento nel database.
    """
    conn = create_db_connection()
    cur = conn.cursor()

    username = register_request.username
    email = register_request.email
    password = register_request.password

    try:
        # Hash della password
        password_bytes = password.encode("utf-8") # converte la password in byte, perché la libreria bcrypt lavora solo con byte
        hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt()) # crea un hash della password usando l’algoritmo bcrypt

        # Inserimento utente nel DB
        cur.execute(
            "INSERT INTO users (username, password_hash, email) VALUES (%s, %s, %s)",
            (username, hashed.decode("utf-8"), email) # decode("utf-8"): converte l’hash da byte a stringa
        )
        conn.commit()

        return RegisterResponse(status="ok")

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=422, detail=f"Errore durante l'inserimento: {e}")

    finally:
        cur.close()
        conn.close()