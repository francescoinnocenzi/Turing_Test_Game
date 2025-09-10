import { getRoomNameFromUrl, showResultModal } from "./utils.js";

// Variabili globali
let ws = null; // WebSocket
let mode = null; // Modalità di gioco
let clientId = Math.floor(Math.random() * 100000); // ID casuale per il client
let currentQuestionId = null; // ID dell'ultima domanda ricevuta
let role = 'PLAYER'; // Ruolo fisso per questa pagina
let currentAnswer = null; // Risposta corrente

// Funzione per impostare e gestire la connessione WebSocket
function setupWebSocket(selectedRoom) {
    mode = "single"; // Modalità fissa per questa pagina

    // Chiudi la WebSocket esistente se attiva
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close();
    }
    // Crea l'URL del WebSocket
    const url = `ws://localhost:8003/ws/${selectedRoom}/${clientId}?role=${role}&mode=${mode}`;
    console.log("Connessione a:", url);
    // Connetti al WebSocket
    ws = new WebSocket(url);
    // Evento quando la connessione viene aperta
    ws.onopen = () => {
        console.log(`Connesso come PLAYER in modalità ${mode}, stanza: ${selectedRoom}`);
        document.getElementById("room-id").textContent = `${selectedRoom.toUpperCase()} - ${mode.toUpperCase()}`;
    };
    // Evento quando si verifica un errore
    ws.onerror = (e) => {
        console.error("Errore WebSocket:", e);
    };
    // Evento quando la connessione viene chiusa
    ws.onclose = (evt) => {
        console.warn("WS chiuso:", evt);
    };
    // Gestione dei messaggi in arrivo
    ws.onmessage = (event) => {
        try {
            let msg = JSON.parse(event.data);
            console.log(msg.type);
            // Gestisci i diversi tipi di messaggi
            if (msg.type === "question") { // Nuova domanda
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
            } else if (msg.type === "final_judgment") { // Giudizio finale
                console.log("Giudizio finale ricevuto:", msg.judgment);
        
                let playerResult = null;
                // Determina il risultato del player in base al giudizio
                if (msg.judgment.includes("GIUDICE ha VINTO")) {
                    playerResult = "PLAYER ha PERSO";
                } else if (msg.judgment.includes("GIUDICE ha PERSO")) {
                    playerResult = "PLAYER ha VINTO";
                }
                
                console.log(playerResult);
                // Mostra il modale del risultato
                if (playerResult) {
                    showResultModal(playerResult, 'single', 'player','PLAYER');
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
            if (messages) {
                const message = document.createElement('li');
                message.textContent = msg.text || event.data;
                messages.appendChild(message);
                messages.scrollTop = messages.scrollHeight;
            }

        }
    };
}
// Inizializza la WebSocket con il room_name dall'URL
const roomName = getRoomNameFromUrl();
setupWebSocket(roomName);

// Gestione dell'invio della risposta
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
        try { // Invia il messaggio al server
            ws.send(JSON.stringify(message));
            input.value = '';
        } catch (error) {
            console.error("Errore nell'invio:", error);
            return false;
        }
    } else {
        return false;
    }

    // Garantisce che la pagina non si ricarichi e la chat continui a funzionare.
    return false;
}

// Funzione per chiudere il modale del risultato
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