import { getRoomNameFromUrl, scrollAllChats, showResultModal } from './utils.js';
// Variabili globali
let ws = null; // WebSocket 
let clientId = Math.floor(Math.random() * 100000); // ID casuale per il client
let role = "JUDGE"; // Ruolo fisso per questa pagina    
let roomName = getRoomNameFromUrl(); // Ottieni il nome della stanza dalla URL
let pendingAnswers = [];  // Buffer per le risposte in arrivo
let questionCounter = 0; // Contatore delle domande inviate
let currentPositions = {}; // Posizioni correnti dei player (left/right)
let lastQuestion = null;  // Ultima domanda inviata

document.getElementById("room-id").textContent = roomName || "Nessuna";

// Connetti WebSocket solo se ho una room valida e gestisco gli eventi WebSocket
if (roomName) {
    const url = `ws://localhost:8003/ws/${roomName}/${clientId}?role=${role}&mode=multi`;
    // Connetti al WebSocket
    ws = new WebSocket(url);
    // Evento quando la connessione viene aperta
    ws.onopen = () =>
        console.log(`Connesso come ${role} nella stanza ${roomName}`);
    // Evento quando arriva un messaggio dal server
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data); // Messaggio ricevuto
        const input = document.getElementById("questionInput");

        const button = document.querySelector(".send-button");

        console.log("Messaggio ricevuto:", data);
        console.log("Ricevuto messaggio:", data.type);
        // Gestisci i diversi tipi di messaggi
        if (data.type === "player_answer") {  // Risposta di un player
            pendingAnswers.push(data);
        } else if (data.type === "time_to_judge") { // Tempo di giudicare
            input.disabled = true;
            button.disabled = true;
            input.placeholder = "Partita giunta al termine...";

            document.getElementById("judgmentContainer").innerHTML = `
            <div class="judgment-form">
            <h3>⚖️ Chi pensi sia UMANO?</h3>
            <div class="judgment-options">
                <label><input type="radio" name="chosen_player" value="A"><span>Player A</span></label>
                <label><input type="radio" name="chosen_player" value="B"><span>Player B</span></label>
            </div>
            <button class="confirm-button" onclick="submitJudgment()">Conferma scelta</button>
            </div>`;
        } else if (data.type === "all_answered") { // Tutti i player hanno risposto
            console.log("Tutti i player hanno risposto!");

            console.log(pendingAnswers);
            // Mostra le risposte nelle chat corrette
            pendingAnswers.forEach((ans) => {
                const li = document.createElement("li");
                li.textContent = ans.text;
                // Determina a quale chat aggiungere la risposta in base al tipo di player
                if (ans.player_type === currentPositions.left.type) { 
                    li.className = "playerA";
                    li.innerHTML = `<strong>A</strong>: ${ans.text}`;
                    document.getElementById("messagesA").appendChild(li);
                } else if (ans.player_type === currentPositions.right.type) {
                    li.className = "playerB";
                    li.innerHTML = `<strong>B</strong>: ${ans.text}`;
                    document.getElementById("messagesB").appendChild(li);
                }
            });

            // Svuota il buffer delle risposte
            pendingAnswers = [];

            scrollAllChats();
            // Riabilita l'input per la prossima domanda
            input.disabled = false;
            input.placeholder = "✍️ Scrivi una domanda...";
            button.disabled = false;
        } else if (data.type === "positions") {  // Mappatura posizioni
            // Salva la mappatura posizioni arrivata dal backend
            currentPositions.left = data.content.left; // "HUMAN" o "BOT"
            currentPositions.right = data.content.right; // "HUMAN" o "BOT"
            console.log("Posizioni aggiornate:", currentPositions);
        } else if (data.type === "final_judgment") { // Giudizio finale
            console.log(data.judgment);

            const patterns = ["GIUDICE ha VINTO", "GIUDICE ha PERSO"];

            // Trova il risultato del giudice, find restituisce il primo elemento che soddisfa la condizione
            const judgeResult = patterns.find((p) => data.judgment.includes(p));

            console.log(judgeResult);
            // Mostra il risultato in un modale personalizzato
            if (judgeResult) {
                showResultModal(judgeResult, 'multi', 'judge_multi','JUDGE');
            }
        } else if (data.type === "players_update") { // Aggiornamento numero di player connessi alla stanza
            const playersCount = document.getElementById("players-count");

            console.log("Player update", data);
            if(data.players === 0) {
                input.disabled = true;
                button.disabled = true;
            } else if(data.players === 1) {
                input.disabled = false;
                button.disabled = false;
            }

            playersCount.textContent = `${data.players}/1`;

            console.log("Players:", data.players, "Input abilitato:", !input.disabled);
        }
    };
}
// Funzione per inviare una domanda del giudice al server
function sendQuestion() {
    const input = document.getElementById("questionInput");
    const button = document.querySelector(".send-button");
    const text = input.value.trim();

    if (!text) return;

    // Aggiungi la domanda nelle due chat PRIMA di inviarla (in modo che le risposte appaiano sotto)
    questionCounter += 1;
    lastQuestion = { text };

    const qLi1 = document.createElement("li");
    qLi1.className = "question-item";
    qLi1.textContent = `Domanda: ${text}`;
    document.getElementById("messagesA").appendChild(qLi1);

    const qLi2 = document.createElement("li");
    qLi2.className = "question-item";
    qLi2.textContent = `Domanda: ${text}`;
    document.getElementById("messagesB").appendChild(qLi2);

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
// Invia la domanda quando si preme "Invio"
document.getElementById("questionInput").addEventListener("keydown", function (event) {
    if (event.key === "Enter") {
        event.preventDefault(); // evita che faccia refresh
        sendQuestion();
    }
});
// Funzione per inviare il giudizio del giudice al server
function submitJudgment() {
    const selected = document.querySelector(
        'input[name="chosen_player"]:checked'
    );
    if (!selected) return alert("Seleziona un giocatore!");
    ws.send(
        JSON.stringify({
            type: "judge_choice",
            chosen_player_human: selected.value,
        })
    );
}
// Rendi le funzioni accessibili globalmente
window.submitJudgment = submitJudgment;
window.sendQuestion = sendQuestion;

// Funzione per chiudere il modale del risultato
function closeResultModal() {
    if (window.currentModal) {
        window.currentModal.remove();
        window.currentModal = null;
    }
}

