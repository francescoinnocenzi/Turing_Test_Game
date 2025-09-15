import { getRoomNameFromUrl, scrollAllChats, showResultModal } from "./utils.js";
// Variabili globali
let ws = null;  // WebSocket
let clientId = Math.floor(Math.random() * 100000); // ID casuale per il client
let lastQuestion = null;  // Ultima domanda inviata
let questionCounter = 0; // Contatore delle domande inviate
let role = "JUDGE"; // Ruolo fisso per questa pagina

// Invio domanda quando si preme "Invio"
document.getElementById("questionInput").addEventListener("keydown", function(e) {
    if (e.key === "Enter") {
        e.preventDefault();
        sendQuestion();
    }
})
// Funzione per impostare e gestire la connessione WebSocket
function setupWebSocket(roomName) {
    const url = `ws://localhost:8003/ws/${roomName}/${clientId}?role=${role}&mode=single`;
    console.log("Connessione a:", url);
    // Connetti al WebSocket
    ws = new WebSocket(url);
    // Evento quando la connessione viene aperta
    ws.onopen = () => {
        document.getElementById("room-id").textContent = roomName;
        // document.getElementById("ws-id").textContent = clientId;
        console.log("Connesso come JUDGE");
    };

    let pendingAnswers = []; // Buffer per le risposte in arrivo
    let currentPositions = {}; // Posizioni correnti dei player (left/right)
    // Gestione dei messaggi in arrivo (server invia un messaggio al client)
    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data); // Messaggio ricevuto

            console.log(data);

            const button = document.querySelector(".send-button");
            const input = document.getElementById("questionInput");
            // Gestisci i diversi tipi di messaggi
            if (data.type === "player_answer") {
                pendingAnswers.push(data); // salva in memoria le risposte
                console.log('pending: ' + pendingAnswers);
            } else if(data.type == "time_to_judge"){ // Tempo di giudicare
                input.disabled = true;
                input.placeholder = "Partita giunta al termine...";
                button.disabled = true;

                const container = document.getElementById("judgmentContainer");
                
                container.innerHTML = `
                    <div class="judgment-form">
                        <h3>⚖️ Chi pensi sia UMANO?</h3>
                        <div class="judgment-options">
                            <label>
                                <input type="radio" name="chosen_player" value="A">
                                <span>Player A</span>
                            </label>
                            <label>
                                <input type="radio" name="chosen_player" value="B">
                                <span>Player B</span>
                            </label>
                        </div>
                        <button class="confirm-button" onclick="submitJudgment()">Conferma scelta</button>
                    </div>
                `;
                
                console.log(data.message);
            } else if (data.type === "positions") { //Posizioni dei player inviarte dal server
                // Aggiorna le posizioni correnti
                currentPositions.left = data.content.left;   // "HUMAN" o "BOT"
                currentPositions.right = data.content.right; // "HUMAN" o "BOT"
                console.log("Posizioni aggiornate:", currentPositions);
                
            } else if(data.type == "final_judgment"){ // Giudizio finale con risultato
                console.log(data.judgment)

                const patterns = ["GIUDICE ha VINTO", "GIUDICE ha PERSO"];
                const judgeResult = patterns.find(p => data.judgment.includes(p));

                console.log(judgeResult);
                // Mostra il risultato in un modale personalizzato
                if (judgeResult) {
                    showResultModal(judgeResult, 'single', 'judge','JUDGE');
                }
            }else if (data.type === "all_answered") { // Tutti i player hanno risposto
                console.log("Tutti i player hanno risposto!");

                console.log(pendingAnswers);

                // Stampa tutte le risposte accumulate
                pendingAnswers.forEach(ans => {
                    const li = document.createElement("li");
                    li.textContent = ans.text;

                    console.log("STAMPA", currentPositions, ans.player_type);
                    // Determina a quale chat aggiungere la risposta in base al tipo di player
                    if (ans.player_type === currentPositions.left.type) { // Se il player_type della risposta corrisponde a quello del giocatore a sinistra appartiene al Player A
                        li.className = "playerA";
                        li.innerHTML = `<strong>A</strong>: ${ans.text}`;
                        document.getElementById("messagesA").appendChild(li);
                    } else if (ans.player_type === currentPositions.right.type) { // altrimenti la risposta appartiene al Player B.
                        li.className = "playerB";
                        li.innerHTML = `<strong>B</strong>: ${ans.text}`;
                        document.getElementById("messagesB").appendChild(li);
                    }

                });

                // Svuota il buffer
                pendingAnswers = [];

                scrollAllChats();

                input.disabled = false;
                input.placeholder = "✍️ Scrivi una domanda...";
                button.disabled = false;

                // Notifica visiva
                const notification = document.createElement('div');
                notification.classList.add('notification');
                notification.textContent = " " + data.message;
                document.querySelector('.container').appendChild(notification);

                // Aggiungi un separatore nelle chat
                const separator1 = document.createElement('div');
                separator1.className = 'round-separator';
                document.getElementById('messagesA').appendChild(separator1);

                const separator2 = document.createElement('div');
                separator2.className = 'round-separator';
                document.getElementById('messagesB').appendChild(separator2);

                // Scroll automatico ai separatori
                document.getElementById('messagesA').scrollTop = document.getElementById('messagesA').scrollHeight;
                document.getElementById('messagesB').scrollTop = document.getElementById('messagesB').scrollHeight;

                // Rimuovi la notifica dopo 7 secondi
                setTimeout(() => {
                    notification.remove();
                }, 7000);
            }

        } catch (err) {
            console.error("Errore parsing messaggio:", err);
        }
    };
}
// Funzione per inviare una domanda al server
function sendQuestion() {
    const input = document.getElementById("questionInput");
    const button = document.querySelector(".send-button");
    const text = input.value.trim();

    if (!text) return;

    // Aggiungi la domanda nelle due chat PRIMA di inviarla (in modo che le risposte appaiano sotto)
    questionCounter += 1;
    lastQuestion = { text };

    const qLi1 = document.createElement('li');
    qLi1.className = 'question-item';
    qLi1.textContent = `Domanda: ${text}`;
    document.getElementById('messagesA').appendChild(qLi1);

    const qLi2 = document.createElement('li');
    qLi2.className = 'question-item';
    qLi2.textContent = `Domanda: ${text}`;
    document.getElementById('messagesB').appendChild(qLi2);

    scrollAllChats(); 

    // Invia la domanda al server
    const msg = { type: "question", text: text };
    ws.send(JSON.stringify(msg));
    console.log("Domanda inviata:", text);

    // Pulisci l'input
    input.value = "";

    input.disabled = true;
    input.placeholder = "⏳ Attendo risposte...";

    button.disabled = true;
}
// Funzione per inviare il giudizio del giudice al server
function submitJudgment() {
    const chosen = document.querySelector('input[name="chosen_player"]:checked');
    if (!chosen) {
        alert("Seleziona un giocatore prima di confermare!");
        return;
    }

    console.log("Giudizio inviato:", chosen.value);

    // Invia solo la scelta al server via WebSocket
    ws.send(JSON.stringify({
        type: "judge_choice",
        chosen_player_human: chosen.value
    }));

    // Blocca ulteriori modifiche
    document.querySelectorAll('input[name="chosen_player"]').forEach(radio => {
        radio.disabled = true;
    });

    // Disabilita visivamente il player NON scelto
    if (chosen === "A") {
        document.querySelector("#messagesB").style.opacity = "0.5";
        document.querySelector("#messagesB").style.pointerEvents = "none";
    } else {
        document.querySelector("#messagesA").style.opacity = "0.5";
        document.querySelector("#messagesA").style.pointerEvents = "none";
    }

    // Disabilita anche il bottone per evitare doppi invii
    document.querySelector(".confirm-button").disabled = true;
}

window.submitJudgment = submitJudgment;
window.sendQuestion = sendQuestion;

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

const roomName = getRoomNameFromUrl();

// Avvia connessione alla stanza di default
setupWebSocket(roomName);