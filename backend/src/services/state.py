'''File per variabili globali condivise'''

user_id: int | None = None

previous_questions = []

chat_history = []

# Dizionario globale (o puoi metterlo dentro un oggetto tipo RoomManager)
room_positions = {}