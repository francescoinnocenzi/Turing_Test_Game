from database.connection import create_db_connection

def handle_scores(user_id: int, session_id: int, mode: str, role : str, win: bool):
    """Aggiorna i punteggi dei giocatori in base al risultato della partita"""
    print(f"🏆 Aggiorno punteggi per User {user_id}, Session {session_id}, Mode {mode}, Role {role}, Win {win}")
    conn = create_db_connection()
    cursor = conn.cursor()

    mode = "MULTIPLAYER" if mode == "multi" else "SINGLEPLAYER"
    #se win = true, il giudice ha vinto e il player ha perso
    try:
       
        judge_score = 0
        human_score = 0

        if mode == "MULTIPLAYER":
            if role == "JUDGE" and win:
                judge_score = 2
                human_score = 0
            elif role == "JUDGE" and not win:
                judge_score = 0
                human_score = 1
            else:
                print("Errore Aggiornamento Punteggi: In multiplayer il ruolo deve essere JUDGE")
                raise ValueError("In multiplayer il ruolo deve essere JUDGE")
            
            # Aggiorna il punteggio del giudice
            cursor.execute("""
                INSERT INTO scores (user_id, session_id, score, mode, player_role)
                VALUES (?, ?, ?, ?, ?)
                """, (user_id, session_id, judge_score, mode, "JUDGE"))
            conn.commit()
            
            print("Recupero ID del player umano...")
            # Recupera l'ID dell'utente PLAYER dalla sessione
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
            """, (player_user_id, session_id, human_score, mode, "HUMAN")) #il player è sempre umano in multiplayer
            conn.commit()

            print(f"✅ Punteggi aggiornati: User {player_user_id}, Session {session_id}, Score {human_score}, Mode {mode}, Role HUMAN")
        elif mode == "SINGLEPLAYER":
            if role == "JUDGE" and win:
                judge_score = 2 #bot
                human_score = 0
            elif role == "JUDGE" and not win:
                judge_score = 0 #bot
                human_score = 1
            elif role == "HUMAN" and win:
                judge_score = 2 #bot
                human_score = 0
            elif role == "HUMAN" and not win:
                judge_score = 0 #bot
                human_score = 1
            else:
                print("Errore Aggiornamento Punteggi: In singleplayer")
            cursor.execute("""
            INSERT INTO scores (user_id, session_id, score, mode, player_role)
            VALUES (?, ?, ?, ?, ?)
            """, (user_id, session_id, human_score, mode, "HUMAN"))
            conn.commit()
        else:
            print("Errore Aggiornamento Punteggi: Modalità sconosciuta")
            raise ValueError("Modalità sconosciuta")    
        
        print(f"✅ Punteggi aggiornati: User {user_id}, Session {session_id}, Score {judge_score}, Mode {mode} , Role JUDGE")

    except Exception as e:
        conn.rollback()
        print(f"Errore nell'aggiornamento punteggi: {e}")
    finally:
        cursor.close()
        conn.close()