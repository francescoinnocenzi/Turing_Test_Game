let room = null;
let ws = null;

const rooms = ['room1', 'room2', 'room3'];
const client_id = Date.now();

document.querySelector("#ws-id").textContent = client_id;

function setupWebSocket(selectedRoom) {
    // Chiude la WebSocket esistente se attiva
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close(); // Questo innesca WebSocketDisconnect sul server
    }
    
    ws = new WebSocket(`ws://localhost:8003/ws/${selectedRoom}/${client_id}`);

    ws.onmessage = function(event) {
        if (typeof ws_onmessage_override === "function") {
            ws_onmessage_override(event);
        } else {
            const messages = document.getElementById('messages');
            const message = document.createElement('li');
            const content = document.createTextNode(event.data);
            message.appendChild(content);
            messages.appendChild(message);
        }
    };


    ws.onopen = () => {
        console.log(`✅ WebSocket connesso a ${selectedRoom}`);
    };

    ws.onerror = (e) => {
        console.error("❌ Errore WebSocket:", e);
    };
}

document.querySelector('#room1').addEventListener('click', () => {
    room = rooms[0];
    console.log("Hai scelto:", room);
    document.querySelector("#room-id").textContent = room;
    setupWebSocket(room);

    // const messages = document.querySelector('#messages');
    // messages.innerHTML = '';
});

document.querySelector('#room2').addEventListener('click', () => {
    room = rooms[1];
    console.log("Hai scelto:", room);
    document.querySelector("#room-id").textContent = room;
    setupWebSocket(room);

    // const messages = document.querySelector('#messages');
    // messages.innerHTML = '';
});

document.querySelector('#room3').addEventListener('click', () => {
    room = rooms[2];
    console.log("Hai scelto:", room);
    document.querySelector("#room-id").textContent = room;
    setupWebSocket(room);

    // const messages = document.querySelector('#messages');
    // messages.innerHTML = '';
});

function sendMessage(event) {
    event.preventDefault();

    const input = document.getElementById("messageText");
    const text = input.value.trim();

    if(!text){
        console.warn("Messaggio vuoto, non inviato");
        return;
    }

    if (ws && ws.readyState === WebSocket.OPEN) {
       const message = {
            type: "question", // Di default è una domanda (per il giudice)
            text: text
        };
        ws.send(JSON.stringify(message)); // Invia JSON
    } else {
        console.warn("WebSocket non connesso.");
    }

    input.value = ''; // Pulisce il campo
}


