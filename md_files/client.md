## PARTE CLIENT (JavaScript)

### Connessione iniziale

Il **client si connette** al server FastAPI tramite WebSocket:

```javascript
var ws = new WebSocket(`ws://localhost:8000/ws/${client_id}`);
```

Questo apre una **connessione persistente** con l’**endpoint WebSocket** del server:
`@app.websocket("/ws/{client_id}")`

---

### Ricezione dei messaggi

Quando il **server invia un messaggio**, viene **triggerato** l’evento `onmessage` nel client:

```javascript
ws.onmessage = function(event) {
  console.log("Messaggio ricevuto:", event.data);
};
```

* Questo evento è del tipo `MessageEvent`
* `event.data` contiene il **messaggio di testo ricevuto**

---

### Invio dei messaggi

Il client invia un messaggio con:

```javascript
ws.send("Ciao!");
```

* Il messaggio viene inviato **tramite WebSocket**, **non** come richiesta HTTP.
* La funzione `send(...)` **non chiama l’endpoint HTTP**, ma invia direttamente **sulla connessione WebSocket aperta**.

---

## Sul lato server (FastAPI)

L’**endpoint WebSocket**:

```python
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    ...
```

* Riceve i messaggi tramite: `data = await websocket.receive_text()`
* Poi può inviare una risposta **privata** con `websocket.send_text(...)`
* Oppure può **inviare a tutti** in **broadcast**