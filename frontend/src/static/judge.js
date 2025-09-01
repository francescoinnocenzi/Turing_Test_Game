import { getRoomNameFromUrl, scrollAllChats, showResultModal } from "./utils.js";

let ws = null;
let clientId = Math.floor(Math.random() * 100000);
let lastQuestion = null;
let questionCounter = 0;

document.getElementById("questionInput").addEventListener("keydown", function(e) {
    if (e.key === "Enter") {
        e.preventDefault();
        sendQuestion();
    }
})

function setupWebSocket(roomName) {
    const url = `ws://localhost:8003/ws/${roomName}/${clientId}?role=JUDGE&mode=single`;
    console.log("🔌 Connessione a:", url);

    ws = new WebSocket(url);

    ws.onopen = () => {
        document.getElementById("room-id").textContent = roomName;
        document.getElementById("ws-id").textContent = clientId;
        console.log("✅ Connesso come JUDGE");
    };

    let pendingAnswers = [];
    let currentPositions = {};
    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);

            console.log(data);

            const button = document.querySelector(".send-button");
            const input = document.getElementById("questionInput");

            if (data.type === "player_answer") {
                pendingAnswers.push(data); // salva in memoria le risposte
                console.log('pending: ' + pendingAnswers);
            } else if(data.type == "time_to_judge"){
                input.disabled = false;
                input.placeholder = "✍️ Scrivi una domanda...";
                button.disabled = false;

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
            } else if (data.type === "positions") {
                // Aggiorna le posizioni correnti
                currentPositions.left = data.content.left;   // "HUMAN" o "BOT"
                currentPositions.right = data.content.right; // "HUMAN" o "BOT"
                console.log("Posizioni aggiornate:", currentPositions);
                
            } else if(data.type == "final_judgment"){
                console.log(data.judgment)

                const patterns = ["GIUDICE ha VINTO", "GIUDICE ha PERSO"];
                const judgeResult = patterns.find(p => data.judgment.includes(p));

                console.log(judgeResult);

                if (judgeResult) {
                    showResultModal(judgeResult, 'single', 'judge');
                }
            }else if (data.type === "all_answered") {//DA SISTEMARE
                console.log("✅ Tutti i player hanno risposto!");

                console.log(pendingAnswers);

                // Stampa tutte le risposte accumulate
                pendingAnswers.forEach(ans => {
                    const li = document.createElement("li");
                    li.textContent = ans.text;

                    if (ans.player_role === currentPositions.left.type) {
                        li.className = "playerA";
                        li.innerHTML = `<strong>A (${ans.player_role})</strong>: ${ans.text}`;
                        document.getElementById("messagesA").appendChild(li);
                    } else if (ans.player_role === currentPositions.right.type) {
                        li.className = "playerB";
                        li.innerHTML = `<strong>B (${ans.player_role})</strong>: ${ans.text}`;
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
                notification.textContent = "✅ " + data.message;
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
            console.error("❌ Errore parsing messaggio:", err);
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
    const qid = `q-${Date.now()}-${questionCounter}`;
    lastQuestion = { id: qid, text };

    const qLi1 = document.createElement('li');
    qLi1.className = 'question-item';
    qLi1.textContent = `Domanda: ${text}`;
    qLi1.setAttribute('data-qid', qid);
    document.getElementById('messagesA').appendChild(qLi1);

    const qLi2 = document.createElement('li');
    qLi2.className = 'question-item';
    qLi2.textContent = `Domanda: ${text}`;
    qLi2.setAttribute('data-qid', qid);
    document.getElementById('messagesB').appendChild(qLi2);

    scrollAllChats(); 

    // Invia la domanda al server (includiamo un qid nel payload)
    const msg = { type: "question", text: text, qid: qid };
    ws.send(JSON.stringify(msg));
    console.log("📨 Domanda inviata:", text);

    // Pulisci l'input
    input.value = "";

    input.disabled = true;
    input.placeholder = "⏳ Attendo risposte...";

    button.disabled = true;
}

function submitJudgment() {
    const chosen = document.querySelector('input[name="chosen_player"]:checked');
    if (!chosen) {
        alert("Seleziona un giocatore prima di confermare!");
        return;
    }

    console.log("📤 Giudizio inviato:", chosen.value);

    // Invia solo la scelta al backend via WebSocket
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


// ✅ NUOVA FUNZIONE: Chiudi modale
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