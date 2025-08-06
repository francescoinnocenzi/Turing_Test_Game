from fastapi import WebSocket
import json

DEFAULT_ROLES = ["JUDGE", "HUMAN", "BOT"]  # Ruoli disponibili in ordine

# Gestore delle connessioni WebSocket
class ConnectionManager:
    def __init__(self):
        # Dizionario che ha come chiave la stanza e come valore un 
        # dict delle connessioni WebSocket attive {client_id: {ws, role}}
        self.rooms: dict[str, dict[int, dict[str, any]]] = {}  # CORRETTO IL TIPO

        # { 
        #  "room1": {1: {"ws": websocket_obj1, "role": "JUDGE"}, 2: {"ws": websocket_obj2, "role": "HUMAN"}, },
        #  "room2": { 3: {"ws": websocket_obj3, "role": "JUDGE"},} 
        # }

    async def connect(self, room_name: str, websocket: WebSocket, client_id: int):
        # Accetta una nuova connessione WebSocket
        print(f"STARTING CONNECTION: room={room_name}, client={client_id}")
        await websocket.accept()
        print(f"WEBSOCKET ACCEPTED: room={room_name}, client={client_id}")

        if room_name not in self.rooms:
            self.rooms[room_name] = {} # creo dizionario associato alla chiave room
            print(f"CREATED NEW ROOM: {room_name}")

        room = self.rooms[room_name]

        if client_id not in room:
            role_index = len(room)
            print(f"ROLE INDEX: {role_index} for client {client_id}")
            if role_index < len(DEFAULT_ROLES):
                role = DEFAULT_ROLES[role_index]
            else:
                role = "SPECTATOR"
            
            room[client_id] = {
                "ws": websocket,
                "role": role
            }
            
            print(f"ASSIGNED ROLE: Client {client_id} → {role}")
        
        print(f"ROOMS STATE: {[(r, list(clients.keys())) for r, clients in self.rooms.items()]}")

    def disconnect(self, room_name: str, client_id: int):
        if room_name in self.rooms and client_id in self.rooms[room_name]:
            # Rimuove una connessione disconnessa dal dizionario
            self.rooms[room_name].pop(client_id, None)

            # Elimina la stanza se vuota
            if not self.rooms[room_name]:
                self.rooms.pop(room_name)
        
        print(f"DISCONNECT - Client {client_id} disconnected from {room_name}")

    async def send_personal_message(self, message: str, room_name: str, client_id: int):
        # Get restituisce valore associato alla chiave, quindi la websocket associata ad un client_id
        client_data = self.rooms.get(room_name, {}).get(client_id)  # CORRETTO

        if client_data:
            # Invia un messaggio solo al client specificato
            await client_data["ws"].send_text(message)
        
    async def broadcast(self, message: str, room_name: str):
        print(f'BROADCAST to {room_name}: {message}')
        # Invia un messaggio a tutti i client connessi nella room
        broadcast_message = json.dumps({
            "type": "system",
            "text": message
        })
        for client_data in self.rooms.get(room_name, {}).values():  # CORRETTO
            await client_data["ws"].send_text(broadcast_message)

    async def send_question_to_players(self, question: str, room_name: str):
        """Invia una domanda dal giudice a tutti i player nella stanza"""
        room = self.rooms.get(room_name, {})
        message = json.dumps({
            "type": "question", 
            "text": question
        })
        
        print(f"SENDING QUESTION '{question}' to players in room {room_name}")
        
        sent_count = 0
        for client_id, client_data in room.items():
            # Invia solo ai player (HUMAN e BOT), non al giudice
            if client_data["role"] in ["HUMAN", "BOT"]:
                await client_data["ws"].send_text(message)
                print(f"  → Sent to client {client_id} ({client_data['role']})")
                sent_count += 1
        
        print(f"Question sent to {sent_count} players")

    async def send_answer_to_judge(self, answer: str, room_name: str, player_number: int):
        """Invia una risposta dal player al giudice"""
        room = self.rooms.get(room_name, {})
        message = json.dumps({
            "type": "answer",
            "text": answer,
            "from": player_number  # 1 per HUMAN, 2 per BOT
        })
        
        print(f"SENDING ANSWER '{answer}' from player {player_number} to judge in room {room_name}")
        
        for client_id, client_data in room.items():
            # Invia solo al giudice
            if client_data["role"] == "JUDGE":
                await client_data["ws"].send_text(message)
                print(f"  → Sent to JUDGE (client {client_id})")
                break

    async def send_to_judge(self, message_data: dict, room_name: str):
        """Invia un messaggio generico al giudice"""
        room = self.rooms.get(room_name, {})
        message = json.dumps(message_data)
        
        print(f"SENDING MESSAGE to judge in room {room_name}: {message_data}")
        
        for client_id, client_data in room.items():
            # Invia solo al giudice
            if client_data["role"] == "JUDGE":
                await client_data["ws"].send_text(message)
                print(f"Sent to JUDGE (client {client_id})")
                break