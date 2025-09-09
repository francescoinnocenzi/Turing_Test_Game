export function getRoomNameFromUrl() {
    const params = new URLSearchParams(window.location.search);
    return params.get("room");
}

export function scrollAllChats() {
    document.querySelectorAll(".chat-box").forEach((box) => (box.scrollTop = box.scrollHeight));
}

export function createSession(bottone, mode, page) {
    bottone.addEventListener("click", async (event) => {
        event.preventDefault();
        try {
            const response = await fetch(
                "http://localhost:8003/create/session",
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    credentials: "include", // Quando chiamo /create/session, il backend ti manda un cookie di sessione. Se non metto "include", quel cookie non verrà mai salvato
                    body: JSON.stringify({ mode: mode }), // Passo il mode
                }
            );

            if (response.ok) {
                const data = await response.json();

                console.log(" Sessione creata:", data);

                // Passo il room_name come query param
                window.location.href =
                    `/${page}?room=` + encodeURIComponent(data.room_name);
            } else {
                console.error("Errore:", response.status, response.statusText);
            }
        } catch (error) {
            console.error("Errore nel recupero della sessione:", error);
        }
    });
}

export function showResultModal(result, mode, page, role) {
    // Determina se ha vinto o perso
    const hasWon = result.includes("VINTO");

    // Crea l'overlay della modale
    const modalOverlay = document.createElement("div");
    modalOverlay.className = `modal-overlay ${
        hasWon ? "result-win" : "result-lose"
    }`;

    // Contenuto della modale
    modalOverlay.innerHTML = `
            <div class="modal-content">
                <span class="result-icon">${hasWon ? "🎉" : "😔"}</span>
                <div class="result-title">${
                    hasWon ? "HAI VINTO!" : "HAI PERSO!"
                }</div>
                <div class="result-details">
                
                    ${getResultMessage(mode, role, hasWon)}
                
                </div>
                
                <a href="/index" class="close-button"">
                    🏠 Torna al Menu
                </a>
                ${page !== "player_multi" ? `<button id="play-again" class="close-button"">
                    🎮 Gioca ancora
                </button>` : ''}
            </div>
        `;

    // Aggiungi al body
    document.body.appendChild(modalOverlay);

function getResultMessage(mode, role, hasWon) {

    if (role === "JUDGE") {
        return hasWon
        ? " Ottimo intuito! Sei riuscito a riconoscere correttamente chi era umano."
        : " Questa volta ti hanno ingannato... hai scambiato il bot per umano o viceversa.";
    }

    return hasWon
        ? " 🥳 “Hai vinto! Il giudice non ha sospettato nulla."
        : " ❌ “Questa volta non ha funzionato: il giudice ti ha smascherato.";
    }


    // Solo se non è player_multi, aggiungi l'event listener per "Gioca ancora"
    if (page !== "player_multi") {
        createSession(document.getElementById("play-again"), mode, page);
    }

    // Salva riferimento per poterla chiudere
    window.currentModal = modalOverlay;

    console.log("Risultato mostrato:", result);
}