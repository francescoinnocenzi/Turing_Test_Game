## PARTE SERVER (Python)

### Classe ConnectionManager

Gestisce le **connessioni WebSocket attive** dei client attraverso un dizionario.

```python
self.active_connections: dict[int, WebSocket] = {}
```

* Ogni **`client_id`** (intero univoco) è associato a una connessione **WebSocket** aperta

---

### Connessione di un **nuovo client**

Accetta una connessione WebSocket e la salva nel dizionario:

```python
async def connect(self, client_id: int, websocket: WebSocket):
    await websocket.accept()
    self.active_connections[client_id] = websocket
```

---

### Disconnessione del client

Rimuove il client dalla lista delle connessioni attive:

```python
def disconnect(self, client_id: int):
    self.active_connections.pop(client_id)
```

---

## Gestione dei messaggi

### Invio a un singolo client

```python
async def send_to_client(self, client_id: int, message: str):
    websocket = self.active_connections.get(client_id)
    if websocket:
        await websocket.send_text(message)
```

* Verifica se il client è connesso  
* Invia il **messaggio di testo** tramite WebSocket

---

### Invio in broadcast a tutti i client

```python
async def broadcast(self, message: str):
    for ws in self.active_connections.values():
        await ws.send_text(message)
```

* Scorre tutte le connessioni attive  
* Invia il messaggio **a ogni client connesso**

---

## Endpoint WebSocket

Gestisce la comunicazione tra client e server:

```python
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(client_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_to_client(client_id, f"You said: {data}")
            await manager.broadcast(f"Client {client_id} says: {data}")
    except WebSocketDisconnect:
        manager.disconnect(client_id)
        await manager.broadcast(f"Client {client_id} disconnected")
```

* Registra la connessione del client  
* Riceve i **messaggi in arrivo**  
* Invia risposte **private** e **broadcast**  
* Gestisce la **disconnessione** in caso di interruzione