const form = document.getElementById("registerForm");
const msg = document.getElementById("msg");

form.addEventListener("submit", async (e) => {
    e.preventDefault();
    msg.style.display = "none";

    const username = form.username.value.trim();
    const email = form.email.value.trim();
    const password = form.password.value;
    const password2 = form.password2.value;

    if (password !== password2) {
        msg.className = "msg err";
        msg.textContent = "Le password non coincidono.";
        msg.style.display = "block";
        return;
    }

    try {
        const res = await fetch(
            "http://localhost:8003/api/register",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    accept: "application/json",
                },
                body: JSON.stringify({ username, email, password }),
            }
        );

        const data = await res.json();
        if (!res.ok)
            throw new Error(
                data.detail || "Errore in registrazione"
            );

        msg.className = "msg ok";
        msg.textContent = "Registrazione completata!";
        msg.style.display = "block";

        // opzionale: redirect automatico al login
        setTimeout(() => {
            window.location.href = "/login";
        }, 900);
    } catch (err) {
        msg.className = "msg err";
        msg.textContent = err.message || "Errore imprevisto";
        msg.style.display = "block";
    }
});