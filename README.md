## Modalità di gioco

### Multiplayer
Due utenti umani partecipano contemporaneamente con ruoli distinti:

- **GIUDICE**: il suo compito è **porre domande** liberamente ai partecipanti.
- **PLAYER (umano)**: risponde alle domande poste dal giudice.
- **CPU (bot)**: risponde anch’essa alle domande del giudice.

Il flusso di gioco è il seguente:
1. Il GIUDICE pone una domanda.
2. Sia il PLAYER umano che la CPU forniscono la loro risposta.
3. Il sistema consegna al GIUDICE le due risposte in forma anonima.
4. Il GIUDICE deve decidere quale delle due appartiene al partecipante umano.

---

### Singleplayer
Un solo utente umano è connesso alla lobby. Sono previste due varianti:

#### Modalità A: Player come giudice
- Il player pone una domanda libera.
- Il sistema mostra due risposte: una generata dalla CPU in tempo reale e una HUMAN.
- La risposta HUMAN può essere:
  - Recuperata da sessioni precedenti tramite ricerca semantica.
  - Oppure generata da un LLM e marcata come HUMAN simulata.

#### Modalità B: Player come HUMAN
- Il sistema propone una sequenza di domande generate da LLM.
- Il player risponde come HUMAN.
- In parallelo, la CPU produce la sua risposta.
- Un giudice virtuale (LLM) valuta le due risposte.

---

## Avvio con Docker Compose

Il progetto comprende i seguenti servizi:
- **Backend** (FastAPI / WebSocket) su porta 8003
- **Frontend** su porta 8001
- **MariaDB** su porta 3307
- **Ollama** su porta 11434

Per avviare l’ambiente:

```bash
docker compose up --build
```

## Nota bene

Il modello AI deve essere scaricato manualmente prima di poter giocare. Se non è disponibile, il backend non riuscirà a generare risposte AI.
Assicurati quindi di lanciare il comando:

```bash
ollama pull gemma3:4b
```
Ollama lo salverà localmente e sarà riutilizzato in tutte le sessioni successive. 

## Attenzione 
Se viene installata una versione diversa di gemma o un altro modello, bisogna 
cambiare il valore della variabile ```model``` situata nel file ```backend/src/services/state.py``` 