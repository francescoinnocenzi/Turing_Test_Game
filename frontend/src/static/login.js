const form = document.getElementById("loginForm");
const msg = document.getElementById("msg");
// Gestione della sottomissione del form di login
form.addEventListener("submit", async (e) => {
    e.preventDefault();
    msg.style.display = "none";

    const payload = {
        identifier: form.identifier.value.trim(),
        password: form.password.value,
    };

    try { // Chiamata al backend per il login
        const res = await fetch("http://localhost:8003/api/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                accept: "application/json",
            },
            credentials: "include",
            body: JSON.stringify(payload),
        });

        const data = await res.json();
        if (!res.ok)
            throw new Error(data.detail || "Errore di accesso");

        msg.className = "msg ok";
        msg.textContent = "Accesso riuscito! 🎉";
        msg.style.display = "block";

        setTimeout(() => {
            window.location.href = "/index";
        }, 800);
    } catch (err) {
        msg.className = "msg err";
        msg.textContent = err.message || "Errore imprevisto";
        msg.style.display = "block";
    }
});
