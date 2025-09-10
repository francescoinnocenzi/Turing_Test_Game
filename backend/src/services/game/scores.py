from database.connection import create_db_connection
from schemas.service_response import ServiceResponse

def handle_scores(user_id: int, session_id: int, mode: str, role : str, win: bool) -> ServiceResponse:
    """
    Inserisce i punteggi dei giocatori nel database in base al risultato della partita.

    Args
        user_id (int): ID dell'utente che ha effettuato l'azione (giudice o player).
        session_id (int): ID della sessione di gioco corrente.
        mode (str): Modalità di gioco, "single" o "multi".
        role (str): Ruolo dell'utente ("PLAYER" o "JUDGE").
        win (bool): Indica se il ruolo specificato ha vinto la partita.

    Returns
        ServiceResponse: Oggetto che indica l'esito dell'operazione ("ok" o "error").

    Raises
        ValueError: Se ci sono incongruenze nei ruoli o modalità sconosciute.
    """
    print(f"Aggiorno punteggi per User {user_id}, Session {session_id}, Mode {mode}, Role {role}, Win {win}")
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

            # Inserisco punteggio player
            cursor.execute("""
                INSERT INTO scores (user_id, session_id, score, mode, player_role) 
                VALUES (?, ?, ?, ?, ?)
            """, (player_user_id, session_id, human_score, mode, "PLAYER"))
            conn.commit()

            print(f"Punteggi aggiornati: User {player_user_id}, Session {session_id}, Score {human_score}, Mode {mode}, Role PLAYER")
        elif mode == "SINGLEPLAYER":
            # win fa riferimento al giudice
            score = 0 #punteggio dell'unico giocatore
            if role == "JUDGE" and win:
                score = 2
            elif role == "JUDGE" and not win:
                score = 0
            elif role == "PLAYER" and win:
                score = 0
            elif role == "PLAYER" and not win:
                score = 1
            else:
                print("Errore Aggiornamento Punteggi: In singleplayer")
            cursor.execute("""
            INSERT INTO scores (user_id, session_id, score, mode, player_role)
            VALUES (?, ?, ?, ?, ?)
            """, (user_id, session_id, score, mode, role))
            conn.commit()
        else:
            print("Errore Aggiornamento Punteggi: Modalità sconosciuta")
            raise ValueError("Modalità sconosciuta")    
        
        print(f"Punteggi aggiornati: User {user_id}, Session {session_id}, Score {judge_score}, Mode {mode} , Role JUDGE")

        return ServiceResponse(status="ok")

    except Exception as e:
        conn.rollback()
        print(f"Errore nell'aggiornamento punteggi: {e}")
        return ServiceResponse(status="error")
    finally:
        cursor.close()
        conn.close()