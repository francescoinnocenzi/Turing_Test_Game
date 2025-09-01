const container = document.getElementById("ranking-container");
const refreshBtn = document.getElementById("refresh-ranking");

async function loadRanking() {
    try {
        container.innerHTML = "<p>Caricamento classifica...</p>";
        const response = await fetch("http://localhost:8003/ranking");
        if (!response.ok) throw new Error("Errore nel recupero della classifica");

        const data = await response.json();
        const ranking = data.ranking;

        if (ranking.length === 0) {
            container.innerHTML = "<p>Nessuna classifica disponibile.</p>";
            return;
        }

        let html = `<table class="ranking-table">
                        <tr>
                            <th>Posizione</th>
                            <th>Username</th>
                            <th>Punteggio</th>
                        </tr>`;

        ranking.forEach((player, index) => {
            html += `<tr>
                        <td>${index + 1}</td>
                        <td>${player.username}</td>
                        <td>${player.total_score}</td>
                    </tr>`;
        });

        html += `</table>`;
        container.innerHTML = html;

    } catch (error) {
        console.error(error);
        container.innerHTML = `<p>Errore nel caricamento della classifica</p>`;
    }
}

// Carica la classifica al caricamento della pagina
window.onload = loadRanking;

// Ricarica la classifica al click
refreshBtn.addEventListener("click", loadRanking);