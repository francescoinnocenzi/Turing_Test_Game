import mariadb
from fastapi import HTTPException
from typing import Union, List, Tuple

# Parametri di connessione al database
DB_HOST = "mariadb"  # Nome del servizio del database
DB_PORT = 3306  # Porta esposta dal docker-compose
DB_USER = "user"  # User dal docker-compose
DB_PASSWORD = "pwd"  # Password dal docker-compose
DB_NAME = "turing_game"

def create_db_connection() -> mariadb.Connection:
    """
    Crea e restituisce una connessione al database.

    Returns
        mariadb.Connection: Oggetto relativo alla connessione del database.

    Raises
        HTTPException: Se la connessione al database fallisce.
    """
    
    try:
        # Creazione della connessione con i parametri forniti
        conn = mariadb.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME
        )
        return conn # Restituisce l'oggetto connessione
    except mariadb.Error as e:
        raise HTTPException(status_code=500, detail=f"Errore nella connessione al database: {str(e)}")