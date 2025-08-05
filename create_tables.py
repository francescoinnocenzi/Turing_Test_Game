#!/usr/bin/env python3
"""
Script per creare le tabelle del database del Turing Test Chat
"""

import mariadb
from backend.src.database.connection import create_db_connection

def create_tables():
    """Crea tutte le tabelle necessarie nel database"""
    
    conn = create_db_connection()
    cursor = conn.cursor()
    
    try:
        print("🔄 Creazione tabelle in corso...")
        
        # Tabella sessions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                room_name VARCHAR(50) NOT NULL,
                judge_id VARCHAR(100),
                human_player_id VARCHAR(100),
                bot_player_id VARCHAR(100),
                status ENUM('waiting', 'active', 'completed') DEFAULT 'waiting',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP NULL,
                UNIQUE KEY unique_room_session (room_name, status)
            )
        """)
        print("✅ Tabella 'sessions' creata")
        
        # Tabella questions (modifica per aggiungere room_name se non esiste già)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                session_id INT,
                text TEXT NOT NULL,
                author_id VARCHAR(100),
                room_name VARCHAR(50) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE SET NULL,
                INDEX idx_session_questions (session_id),
                INDEX idx_room_questions (room_name)
            )
        """)
        
        # Aggiungi room_name alla tabella questions se non esiste
        try:
            cursor.execute("ALTER TABLE questions ADD COLUMN room_name VARCHAR(50) NOT NULL DEFAULT ''")
            print("✅ Colonna 'room_name' aggiunta alla tabella 'questions'")
        except mariadb.Error:
            pass  # La colonna esiste già
            
        print("✅ Tabella 'questions' verificata/aggiornata")
        
        # Tabella answers
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS answers (
                id INT AUTO_INCREMENT PRIMARY KEY,
                question_id INT NOT NULL,
                session_id INT NOT NULL,
                text TEXT NOT NULL,
                author_id VARCHAR(100) NOT NULL,
                author_type ENUM('HUMAN', 'BOT') NOT NULL,
                room_name VARCHAR(50) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
                INDEX idx_question_answers (question_id),
                INDEX idx_session_answers (session_id),
                INDEX idx_room_answers (room_name)
            )
        """)
        print("✅ Tabella 'answers' creata")
        
        # Indici aggiuntivi
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_room_status ON sessions(room_name, status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_questions_created_at ON questions(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_answers_created_at ON answers(created_at)")
        print("✅ Indici aggiuntivi creati")
        
        # Vista session_details
        cursor.execute("""
            CREATE OR REPLACE VIEW session_details AS
            SELECT 
                s.id as session_id,
                s.room_name,
                s.judge_id,
                s.human_player_id,
                s.bot_player_id,
                s.status,
                s.created_at as session_created,
                s.completed_at,
                COUNT(DISTINCT q.id) as total_questions,
                COUNT(DISTINCT a.id) as total_answers
            FROM sessions s
            LEFT JOIN questions q ON s.id = q.session_id
            LEFT JOIN answers a ON s.id = a.session_id
            GROUP BY s.id, s.room_name, s.judge_id, s.human_player_id, s.bot_player_id, 
                     s.status, s.created_at, s.completed_at
        """)
        print("✅ Vista 'session_details' creata")
        
        conn.commit()
        print("\n🎉 Tutte le tabelle sono state create/aggiornate con successo!")
        
    except mariadb.Error as e:
        conn.rollback()
        print(f"❌ Errore durante la creazione delle tabelle: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    create_tables()
