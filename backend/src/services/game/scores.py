from database.connection import create_db_connection

def handle_scores(user_id: int, session_id: int, mode: str, role : str, win: bool):
    """Aggiorna i punteggi dei giocatori in base al risultato della partita"""
    conn = create_db_connection()
    cursor = conn.cursor()

    try:
        if mode== "single":
            if win and role == "HUMAN":
                score = 1
            elif win and role == "JUDGE":
                score = 2
            else:
                score = 0
            
            cursor.execute("""
                INSERT INTO scores (user_id, session_id, score, mode, player_role)
                VALUES (?, ?, ?, ?,?)
            """, (user_id, session_id, score, "SINGLEPLAYER",role))
        else:
            raise Exception("Modalità non supportata per il calcolo punteggi")

        conn.commit()
        print(f"✅ Punteggi aggiornati: User {user_id}, Session {session_id}, Score {score}, Mode {mode}")

    except Exception as e:
        conn.rollback()
        print(f"Errore nell'aggiornamento punteggi: {e}")
    finally:
        cursor.close()
        conn.close()