//Funzioni per la gestione del multiplayer

// Funzione per creare una nuova sessione come giudice
async function createJudgeSession() {
    try { // Chiamata al backend per creare una nuova sessione
        const response = await fetch("http://localhost:8003/create/session", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({ mode: "multi" }) // Passo il mode
        });
        if (!response.ok) throw new Error("Errore creazione sessione");
        const data = await response.json();
        window.location.href = "/judge_multi?room=" + encodeURIComponent(data.room_name);
    } catch (e) {
        alert("Errore: " + e.message);
    }
}
// Funzione per aprire il modale di join stanza
function openModal() {
    document.getElementById("modalOverlay").style.display = "flex";
    loadRooms();
}
// Funzione per chiudere il modale di join stanza
function closeModal() {
    document.getElementById("modalOverlay").style.display = "none";
}
// Funzione per caricare le stanze disponibili dal backend
async function loadRooms() {
    const roomList = document.getElementById("roomList");
    roomList.innerHTML = "<li>Caricamento...</li>";
    try { // Chiamata al backend per ottenere le stanze disponibili
        const response = await fetch("http://localhost:8003/available/sessions", {
            credentials: "include"
        });
        if (!response.ok) throw new Error("Errore caricamento stanze");
        const data = await response.json();
        roomList.innerHTML = "";

        if (data.available_sessions.length === 0) {
            roomList.innerHTML = "<li>Nessuna stanza disponibile</li>";
            return;
        }

        data.available_sessions.forEach(session => {
            const li = document.createElement("li");
            li.textContent = session.room_name;
            li.onclick = () => joinRoom(session.room_name);
            roomList.appendChild(li);
        });
    } catch (e) {
        roomList.innerHTML = "<li>Errore: " + e.message + "</li>";
    }
}

// Funzione per unirsi a una stanza esistente
async function joinRoom(roomName) {
    try { // Chiamata al backend per unirsi alla stanza
        const response = await fetch(`http://localhost:8003/join/session/${roomName}`, {
            method: "POST",
            credentials: "include"
        });

        if (response.status === 409) {
            alert("La stanza è già occupata, scegline un’altra.");
            return;
        }

        if (!response.ok) throw new Error("Errore join sessione");

        window.location.href = "/player_multi?room=" + encodeURIComponent(roomName);
    } catch (e) {
        alert("Errore: " + e.message);
    }
}

// Rendi le funzioni globali per l'HTML inline
window.createJudgeSession = createJudgeSession;
window.openModal = openModal;
window.closeModal = closeModal;
window.loadRooms = loadRooms;
