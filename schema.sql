CREATE TABLE IF NOT EXISTS bot_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    username VARCHAR(255),
    message TEXT,
    timestamp TIMESTAMP,
    command VARCHAR(255),
    game VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS bot_management (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER,
    message TEXT,
    timestamp TIMESTAMP
);

CREATE TABLE IF NOT EXISTS wishes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    wish TEXT
);