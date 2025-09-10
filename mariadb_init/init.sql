-- Comandi SQL per creare le tabelle del database Turing Test Chat

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,          -- ID univoco utente
    username VARCHAR(50) NOT NULL UNIQUE,       -- username univoco
    email VARCHAR(100) NOT NULL UNIQUE,         -- email univoca
    password_hash VARCHAR(255) NOT NULL        -- password (hashed, es. bcrypt)
);

-- Tabella sessions (sessioni di gioco)
CREATE TABLE IF NOT EXISTS sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    room_name VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_available BOOLEAN NOT NULL DEFAULT TRUE,
    mode ENUM('SINGLEPLAYER', 'MULTIPLAYER'),
    UNIQUE (room_name)
);


-- Tabella questions (domande del giudice)
CREATE TABLE IF NOT EXISTS questions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id INT NOT NULL,
    text TEXT NOT NULL,
    room_name VARCHAR(50) NOT NULL,
    author_user_id INT NULL,  -- se AUTORE è BOT, author_user_id è NULL
    author_type ENUM('HUMAN', 'BOT') NOT NULL,
    embedding JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (author_user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Tabella answers (risposte dei partecipanti)
CREATE TABLE IF NOT EXISTS answers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    question_id INT NOT NULL,
    session_id INT NOT NULL,
    text TEXT NOT NULL,
    room_name VARCHAR(50) NOT NULL,
    author_user_id INT NULL, -- se AUTORE è BOT, author_user_id è NULL
    author_type ENUM('HUMAN', 'BOT', 'BOT_AS_HUMAN') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (author_user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS judgments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id INT NOT NULL,
    judge_id INT NOT NULL,
    chosen_player_human VARCHAR(20) NOT NULL,
    is_correct BOOLEAN NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);



CREATE TABLE scores (
    id_score INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    session_id INT NOT NULL,
    score INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    mode ENUM('SINGLEPLAYER', 'MULTIPLAYER') NOT NULL,
    player_role ENUM('PLAYER', 'JUDGE') NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);