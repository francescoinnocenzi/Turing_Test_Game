import { getRoomNameFromUrl, showResultModal } from "./utils.js";

let ws = null;
let clientId = Math.floor(Math.random()*100000);
let role = 'HUMAN'; 
let pendingQuestions = [];
let currentQuestionId = null;

let roomName = getRoomNameFromUrl();
if (!roomName) {
    alert("Nessuna stanza trovata nell’URL!");
    throw new Error("Room non trovata");
}

// Mostra info su pagina
document.getElementById("room-id").textContent = roomName;

// Connetti al WebSocket
const url = `ws://localhost:8003/ws/${roomName}/${clientId}?role=${role}&mode=multi`;
ws = new WebSocket(url);

ws.onopen = () => console.log(`Connesso come ${role} in modalità multi nella stanza ${roomName}`);

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    // Ricezione domanda
    if(data.type === "question"){
        console.log("Domanda ricevuta:", data.text);
        pendingQuestions.push(data.text);
        const qBox = document.getElementById("current-question");
        qBox.textContent = "❓ " + data.text;
        enableForm();

        if (data.question_id) {
            currentQuestionId = data.question_id;
        }
    }

    // Fine round
    else if(data.type === "all_answered" && Array.isArray(data.answers)){
        pendingQuestions = [];
        disableForm();
        document.getElementById("current-question").textContent = "⏳ In attesa di una nuova domanda...";
    }

    // Gioco terminato
    else if(data.type === "final_judgment"){
        console.log("Giudizio finale ricevuto:", data.judgment);

        let playerResult = null;

        if (data.judgment.includes("GIUDICE ha VINTO")) {
            playerResult = "PLAYER ha PERSO";
        } else if (data.judgment.includes("GIUDICE ha PERSO")) {
            playerResult = "PLAYER ha VINTO";
        }

        if (playerResult) {
            showResultModal(playerResult, 'multi', 'player_multi');
        }
    }
};

function enableForm(){
    document.getElementById("messageText").disabled = false;
    document.querySelector(".send-button").disabled = false;
    document.getElementById("messageText").placeholder = "✍️ Scrivi la tua risposta...";
}

function disableForm(){
    document.getElementById("messageText").disabled = true;
    document.querySelector(".send-button").disabled = true;
    document.getElementById("messageText").placeholder = "⏳ Attendi la domanda del giudice...";
}

// 🚀 Invio risposta al server
document.getElementById("messageForm").addEventListener("submit", (e) => {
    e.preventDefault(); // evita reload form
    const input = document.getElementById("messageText");
    const answer = input.value.trim();

    if(answer && ws.readyState === WebSocket.OPEN){
        ws.send(JSON.stringify({
            type: "answer",
            from: clientId,
            text: answer,
            question_id: currentQuestionId
        }));
        console.log("Risposta inviata:", answer);

        // reset input
        input.value = "";
        disableForm();
    }
});
