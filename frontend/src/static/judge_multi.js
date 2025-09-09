import { getRoomNameFromUrl, scrollAllChats, showResultModal } from './utils.js';

let ws = null;
let clientId = Math.floor(Math.random() * 100000);
let role = "JUDGE";
let roomName = getRoomNameFromUrl();
let pendingAnswers = [];
let questionCounter = 0;
let currentPositions = {};
let lastQuestion = null;

document.getElementById("room-id").textContent = roomName || "Nessuna";

// Connetti WebSocket solo se ho una room valida
if (roomName) {
    const url = `ws://localhost:8003/ws/${roomName}/${clientId}?role=${role}&mode=multi`;
    ws = new WebSocket(url);

    ws.onopen = () =>
        console.log(`Connesso come ${role} nella stanza ${roomName}`);

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        const input = document.getElementById("questionInput");

        const button = document.querySelector(".send-button");

        console.log("Messaggio ricevuto:", data);
        console.log("Ricevuto messaggio:", data.type);

        if (data.type === "player_answer") {
            pendingAnswers.push(data);
        } else if (data.type === "time_to_judge") {
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
        } else if (data.type === "all_answered") {
            console.log("Tutti i player hanno risposto!");

            console.log(pendingAnswers);

            pendingAnswers.forEach((ans) => {
                const li = document.createElement("li");
                li.textContent = ans.text;

                if (ans.player_type === currentPositions.left.type) {
                    li.className = "playerA";
                    li.innerHTML = `<strong>A (${ans.player_type})</strong>: ${ans.text}`;
                    document.getElementById("messagesA").appendChild(li);
                } else if (ans.player_type === currentPositions.right.type) {
                    li.className = "playerB";
                    li.innerHTML = `<strong>B (${ans.player_type})</strong>: ${ans.text}`;
                    document.getElementById("messagesB").appendChild(li);
                }
            });

            // Svuota il buffer
            pendingAnswers = [];

            scrollAllChats();

            input.disabled = false;
            input.placeholder = "✍️ Scrivi una domanda...";
            button.disabled = false;
        } else if (data.type === "positions") {
            // Salva la mappatura arrivata dal backend
            // Aggiorna le posizioni correnti
            currentPositions.left = data.content.left; // "HUMAN" o "BOT"
            currentPositions.right = data.content.right; // "HUMAN" o "BOT"
            console.log("Posizioni aggiornate:", currentPositions);
        } else if (data.type === "final_judgment") {
            console.log(data.judgment);

            const patterns = ["GIUDICE ha VINTO", "GIUDICE ha PERSO"];

            // Trova il risultato del giudice, find restituisce il primo elemento che soddisfa la condizione
            const judgeResult = patterns.find((p) => data.judgment.includes(p));

            console.log(judgeResult);

            if (judgeResult) {
                showResultModal(judgeResult, 'multi', 'judge_multi','JUDGE');
            }
        } else if (data.type === "players_update") {
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

    // Invia la domanda al server (includiamo un qid nel payload)
    const msg = { type: "question", text: text };
    ws.send(JSON.stringify(msg));
    console.log("Domanda inviata:", text);

    // Pulisci l'input
    input.value = "";

    input.disabled = true;
    input.placeholder = "⏳ Attendo risposte...";

    button.disabled = true;
}

document.getElementById("questionInput").addEventListener("keydown", function (event) {
    if (event.key === "Enter") {
        event.preventDefault(); // evita che faccia refresh
        sendQuestion();
    }
});

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

window.submitJudgment = submitJudgment;
window.sendQuestion = sendQuestion;


function closeResultModal() {
    if (window.currentModal) {
        window.currentModal.remove();
        window.currentModal = null;
    }
}

