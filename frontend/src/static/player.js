import { getRoomNameFromUrl, showResultModal } from "./utils.js";


let ws = null;
let mode = null;
let clientId = Math.floor(Math.random() * 100000);
let currentQuestionId = null;
let currentAnswer = null;


function setupWebSocket(selectedRoom) {
    mode = "single";

    // Chiudi la WebSocket esistente se attiva
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close();
    }

    const url = `ws://localhost:8003/ws/${selectedRoom}/${clientId}?role=HUMAN&mode=${mode}`;
    console.log("Connessione a:", url);

    ws = new WebSocket(url);

    ws.onopen = () => {
        console.log(`Connesso come HUMAN in modalità ${mode}, stanza: ${selectedRoom}`);
        document.getElementById("room-id").textContent = `${selectedRoom.toUpperCase()} - ${mode.toUpperCase()}`;
    };

    ws.onerror = (e) => {
        console.error("Errore WebSocket:", e);
    };

    ws.onclose = (evt) => {
        console.warn("WS chiuso:", evt);
    };

    ws.onmessage = (event) => {
        try {
            let msg = JSON.parse(event.data);
            console.log(msg.type);
            
            if (msg.type === "question") {
                const questionDiv = document.getElementById("current-question");
                questionDiv.innerHTML = `<span class="emoji">❓</span>Domanda: ${msg.text}`;
                questionDiv.className = "current-question new-question";

                const input = document.getElementById("messageText");
                input.disabled = false;
                input.placeholder = "💬 Scrivi la risposta qui..."

                const sendBtn = document.querySelector('.send-button');
                sendBtn.disabled = false;

                if (msg.question_id) {
                    currentQuestionId = msg.question_id;
                }

                console.log(currentQuestionId);

                setTimeout(() => {
                    questionDiv.className = "current-question";
                }, 2000);
            } else if (msg.type === "final_judgment") {
                console.log("Giudizio finale ricevuto:", msg.judgment);
            
                const patterns = ["HUMAN ha VINTO", "HUMAN ha PERSO"];
                const humanResult = patterns.find(p => msg.judgment.includes(p));

                if (humanResult) {
                    showResultModal(humanResult, 'single', 'player');
                }
                        
            } else {
                const messages = document.getElementById('messages');
                const message = document.createElement('li');
                message.textContent = msg.text || event.data;
                messages.appendChild(message);
                messages.scrollTop = messages.scrollHeight;
            }
        } catch (e) {
            const messages = document.getElementById('messages');
            const message = document.createElement('li');
            message.textContent = event.data;
            messages.appendChild(message);
            messages.scrollTop = messages.scrollHeight;
        }
    };
}

const roomName = getRoomNameFromUrl();

window.onload = function(){
    setupWebSocket(roomName);
}

// --- invio messaggi ---
document.getElementById('messageForm').addEventListener('submit', sendMessage);

function sendMessage(event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }

    const sendBtn = document.querySelector('.send-button');
    sendBtn.disabled = true;

    const input = document.getElementById("messageText");
    input.disabled = true;
    input.placeholder = "⏳ Attendi la domanda del giudice...";
    const text = input.value.trim();

    if (!text) {
        console.warn("Messaggio vuoto, non inviato");
        return false;
    }

    if (ws && ws.readyState === WebSocket.OPEN) {
        currentAnswer = text;
        const message = { type: "answer", text: currentAnswer};
        if (currentQuestionId) {
            message.question_id = currentQuestionId;
        }
        try {
            ws.send(JSON.stringify(message));
            input.value = '';
        } catch (error) {
            console.error("Errore nell'invio:", error);
            return false;
        }
    } else {
        return false;
    }

    return false;
}



// NUOVA FUNZIONE: Chiudi modale
function closeResultModal() {
    if (window.currentModal) {
        window.currentModal.remove();
        window.currentModal = null;
    }
}

// Chiudi modale anche cliccando sull'overlay
document.addEventListener('click', function(event) {
    if (event.target.classList.contains('modal-overlay')) {
        closeResultModal();
    }
});