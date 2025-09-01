const modalitaA = document.querySelector('.mode-a-button');

modalitaA.addEventListener('click', async (event) => {
    event.preventDefault();
    try {
        const response = await fetch("http://localhost:8003/create/session", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            credentials: "include", // Quando chiamo /create/session, il backend ti manda un cookie di sessione. Se non metto "include", quel cookie non verrà mai salvato
            body: JSON.stringify({ mode: "single" }) // Passo il mode
        });

        if (response.ok) {
            const data = await response.json();

            console.log("✅ Sessione creata:", data);
            console.log("🔄 Ora vado a /judge...");
            
            // 👉 Passo il room_name come query param
            window.location.href = "/judge?room=" + encodeURIComponent(data.room_name);

        } else {
            console.error("Errore:", response.status, response.statusText);
        }
    } catch (error) {
        console.error("Errore nel recupero della sessione:", error);
    }
});


const modalitaB = document.querySelector('.mode-b-button');

modalitaB.addEventListener('click', async (event) => {
    event.preventDefault();
    try {
        const response = await fetch("http://localhost:8003/create/session", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            credentials: "include",// Quando chiamo /create/session, il backend ti manda un cookie di sessione. Se non metto "include", quel cookie non verrà mai salvato
            body: JSON.stringify({ mode: "single" }) // Passo il mode
        });

        if (response.ok) {
            const data = await response.json();
            console.log("✅ Sessione creata:", data);
            console.log("🔄 Ora vado a /player...");

            window.location.href = "/player?room=" + encodeURIComponent(data.room_name);
        } else {
            console.error("Errore:", response.status, response.statusText);
        }
    } catch (error) {
        console.error("Errore nel recupero della sessione:", error);
    }
});
