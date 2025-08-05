-- Comandi SQL per creare le tabelle del database Turing Test Chat

-- Tabella sessions (sessioni di gioco)
CREATE TABLE IF NOT EXISTS sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    room_name VARCHAR(50) NOT NULL
    -- judge_id VARCHAR(100),
    -- human_player_id VARCHAR(100),
    -- bot_player_id VARCHAR(100),
    -- status ENUM('waiting', 'active', 'completed') DEFAULT 'waiting',
    -- created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- UNIQUE KEY unique_room_session (room_name, status)
);

-- Tabella questions (domande del giudice)
CREATE TABLE IF NOT EXISTS questions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id INT NOT NULL,
    text TEXT NOT NULL,
    author_id VARCHAR(100) NOT NULL,
    room_name VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE    
);

-- Tabella answers (risposte dei partecipanti)
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
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);