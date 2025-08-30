from database.connection import create_db_connection

def handle_scores(user_id: int, session_id: int, mode: str, role : str, win: bool):
    """Aggiorna i punteggi dei giocatori in base al risultato della partita"""
    conn = create_db_connection()
    cursor = conn.cursor()

    mode = "MULTIPLAYER" if mode == "multi" else "SINGLEPLAYER"

    try:
        if win and role == "HUMAN":
            score = 1
        elif win and role == "JUDGE":
            score = 2
        else:
            score = 0

        if mode == "MULTIPLAYER":
            print("Recupero ID del player umano...")

            score = 1 if win else 0

            cursor.execute("""
                SELECT a.author_user_id
                FROM sessions s JOIN answers a ON s.id = a.session_id
                WHERE s.id = ? AND a.author_user_id IS NOT NULL;
            """, (session_id, ))
        
            row = cursor.fetchone()  # Recupera l'ID del player umano
            
            player_user_id = row[0] if row else None

            cursor.execute("""
                INSERT INTO scores (user_id, session_id, score, mode, player_role) 
                VALUES (?, ?, ?, ?, ?)
            """, (player_user_id, session_id, score, mode, role))

            print(f"✅ Punteggi aggiornati: User {player_user_id}, Session {session_id}, Score {score}, Mode {mode}")

        cursor.execute("""
            INSERT INTO scores (user_id, session_id, score, mode, player_role)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, session_id, score, mode, role))

        conn.commit()
        print(f"✅ Punteggi aggiornati: User {user_id}, Session {session_id}, Score {score}, Mode {mode}")

    except Exception as e:
        conn.rollback()
        print(f"Errore nell'aggiornamento punteggi: {e}")
    finally:
        cursor.close()
        conn.close()