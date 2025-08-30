from schemas.register import RegisterRequest, RegisterResponse
from database.connection import create_db_connection
from fastapi import HTTPException
import bcrypt

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