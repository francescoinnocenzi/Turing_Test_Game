from fastapi import WebSocket
import json


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

    async def connect(self, room_name: str, websocket: WebSocket, client_id: int, role: str):
        """
        Accetta una nuova connessione WebSocket.

        Args
            room_name (str): Il nome della stanza a cui ci si sta connettendo.
            websocket (WebSocket): L'oggetto WebSocket per la connessione.
            client_id (int): L'ID del client che si sta connettendo.
            role (str): Il ruolo del client (es. "HUMAN", "BOT").
        
        Returns
            None
        """
        # Accetta una nuova connessione WebSocket
        print(f"STARTING CONNECTION: room={room_name}, client={client_id}")
        await websocket.accept()
        print(f"WEBSOCKET ACCEPTED: room={room_name}, client={client_id}")

        if room_name not in self.rooms:
            self.rooms[room_name] = {} # creo dizionario associato alla chiave room
            print(f"CREATED NEW ROOM: {room_name}")

        room = self.rooms[room_name]

        if client_id not in room:
            room[client_id] = {
                "ws": websocket,
                "role": role.upper()
            }
            
            print(f"ASSIGNED ROLE: Client {client_id} → {role}")
        
        print(f"ROOMS STATE: {[(r, list(clients.keys())) for r, clients in self.rooms.items()]}")

    def disconnect(self, room_name: str, client_id: int):
        """
        Gestisce la disconnessione di un client da una stanza.

        Args
            room_name (str): Il nome della stanza da cui ci si sta disconnettendo.
            client_id (int): L'ID del client che si sta disconnettendo.

        Returns
            None
        """
        if room_name in self.rooms and client_id in self.rooms[room_name]:
            # Rimuove una connessione disconnessa dal dizionario
            self.rooms[room_name].pop(client_id, None)

            # Elimina la stanza se vuota
            if not self.rooms[room_name]:
                self.rooms.pop(room_name)
        
        print(f"DISCONNECT - Client {client_id} disconnected from {room_name}")

        
    async def broadcast(self, message: str, room_name: str):
        """
        Invia un messaggio a tutti i client connessi nella stanza specificata.

        Args
            message (str): Il messaggio da inviare.
            room_name (str): Il nome della stanza a cui inviare il messaggio.

        Returns
            None
        """
        print(f'BROADCAST to {room_name}: {message}')
        # Invia un messaggio a tutti i client connessi nella room
        broadcast_message = json.dumps({
            "type": "system",
            "text": message
        })
        for client_data in self.rooms.get(room_name, {}).values():  # CORRETTO
            await client_data["ws"].send_text(broadcast_message)

    async def send_question_to_players(self, question: str, room_name: str, question_id: int):
        """
        Invia una domanda dal giudice a tutti i player nella stanza

        Args
            question (str): La domanda da inviare.
            room_name (str): Il nome della stanza a cui inviare la domanda.
            question_id (int): L'ID della domanda.

        Returns
            None
        """
        room = self.rooms.get(room_name, {})
        message = json.dumps({
            "type": "question", 
            "text": question,
            "question_id": question_id
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

    async def send_answer_to_judge(self, answer: str, room_name: str, player_role: int):
        """
        Invia una risposta dal player al giudice

        Args
            answer (str): La risposta da inviare.
            room_name (str): Il nome della stanza da cui inviare la risposta.
            player_role (int): Il ruolo del player che invia la risposta.

        Returns
            None
        """
        # Trova tutti i client con ruolo JUDGE nella room
        for client_id, client_data in self.rooms.get(room_name, {}).items():
            if client_data["role"] == "JUDGE":
                # Invia un messaggio strutturato in JSON invece di testo semplice
                try:
                    message = {
                        "type": "player_answer",
                        "player_role": player_role,
                        "text": answer
                    }
                    await client_data["ws"].send_text(json.dumps(message))
                    print(f"Answer sent to judge (client {client_id})")
                except Exception as e:
                    print(f"Error sending to judge: {e}")

    async def send_positions_to_judge(self, room_name: str, positions: dict):
        """
        Invia al judge la mappatura delle posizioni dei player

        Args
            room_name (str): Il nome della stanza a cui inviare le posizioni.
            positions (dict): Un dizionario contenente le posizioni dei player.

        Returns
            None
        """
       
        # Trova tutti i client con ruolo JUDGE nella room
        for client_id, client_data in self.rooms.get(room_name, {}).items():
            if client_data["role"] == "JUDGE":
                # Invia un messaggio strutturato in JSON invece di testo semplice
                try:
                    message = {
                        "type": "positions",
                        "content": positions
                    }
                    await client_data["ws"].send_text(json.dumps(message))
                    print(f"Positions sent to judge (client {client_id})")
                except Exception as e:
                    print(f"Error sending to judge: {e}")
                    
    async def send_to_judge(self, message: dict, room_name: str):
        """
        Invia un messaggio al giudice

        Args
            message (dict): Il messaggio da inviare.
            room_name (str): Il nome della stanza a cui inviare il messaggio.

        Returns
            None
        """
        # Trova tutti i client con ruolo JUDGE nella room
        for client_id, client_data in self.rooms.get(room_name, {}).items():
            if client_data["role"] == "JUDGE":
                try:
                    await client_data["ws"].send_text(json.dumps(message))
                    print(f"Message sent to judge (client {client_id})")
                except Exception as e:
                    print(f"Error sending to judge: {e}")

    async def send_judgment_to_all(self, judgment: str, room_name: str):
        """
        Invia il giudizio finale a tutti i client nella room

        Args
            judgment (str): Il giudizio finale da inviare.
            room_name (str): Il nome della stanza a cui inviare il giudizio.

        Returns
            None
        """
        room = self.rooms.get(room_name, {})
        message = json.dumps({
            "type": "final_judgment",
            "judgment": judgment
        })
        
        print(f"SENDING JUDGMENT to all clients in room {room_name}")
        
        for client_id, client_data in room.items():
            try:
                await client_data["ws"].send_text(message)
                print(f"  → Judgment sent to client {client_id} ({client_data['role']})")
            except Exception as e:
                print(f"Error sending judgment to client {client_id}: {e}")
    
    async def send_message_to_all(self, message: str, message_type: str, room_name: str):
        """
        Invia messaggio a tutti i client nella room

        Args
            message (str): Il messaggio da inviare.
            message_type (str): Il tipo di messaggio da inviare.
            room_name (str): Il nome della stanza a cui inviare il messaggio.

        Returns
            None
        """
        room = self.rooms.get(room_name, {})
        message = json.dumps({
            "type": f"{message_type}",
            "message": message
        })
        
        print(f"SENDING message to all clients in room {room_name}")
        
        for client_id, client_data in room.items():
            try:
                await client_data["ws"].send_text(message)
                print(f"  → Message sent to client {client_id} ({client_data['role']})")
            except Exception as e:
                print(f"Error sending message to client {client_id}: {e}")


