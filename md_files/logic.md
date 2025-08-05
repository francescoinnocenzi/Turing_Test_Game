# Turing Test Game

### Possibili scenari di gioco:

1. **2 player**:

   * uno è **GIUDICE**, l'altro è **HUMAN**, la CPU è bot.
   * oppure: uno è **HUMAN**, l'altro finge di essere CPU, la CPU fa da **GIUDICE**.

2. **1 solo player in lobby**: qui viene il punto più interessante.


## Come gestire il caso con **1 solo player umano**?

### Modalità A: Il player fa da GIUDICE

**Setup:**

* Il sistema mostra due risposte: una della CPU e una umana (presa da sessioni precedenti).
* Il player deve decidere quale è la risposta umana.

**Pro:**
* Le domande sono completamente **nuove** (no vincoli da DB).
* Buon uso dei dati passati.

**Contro:**

* Hai bisogno di una **libreria di risposte umane** già pronte (registrate da sessioni <precedenti) **a domande simili o generiche** (basata su embedding semantico).
* Se la domanda non è presente (nemmeno domande simili), non ho la risposta umana associata nel db. Potrei generare risposta con un LLM **etichettata come HUMAN**.

---

**Player GIUDICE fa domanda arbitraria** <br>
  **1.** CPU risponde in tempo reale \
  **2.** CERCA risposta HUMAN da archivio:

* Se esiste: mostra quella.

* Se no: genera una finta risposta HUMAN (LLM)

* Salva domanda + risposte per uso futuro

Etichetta internamente se una risposta è simulata o reale, per allenamento futuro o quality check.

---

### Modalità B: Il player risponde come HUMAN


**Setup:**

* Il sistema mostra una sequenza di domande (simulate da sessioni precedenti o da un LLM).
* Il player risponde.
* In parallelo, la CPU risponde anche lei.
* Un **giudice virtuale**, come un LLM, valuta le risposte.

**Pro:**

* Il player ha libertà totale di rispondere.
* Le domande sono controllate (generiche e già testate), quindi si può sempre confrontare con CPU.

**Contro:**

* Il player non può scegliere liberamente le domande.
* Dipende da un archivio di domande già note (oppure da una generazione intelligente).

**Soluzione:**

* Sistema propone domande una per volta (da archivio o da LLM).
* Dopo ogni risposta: si mostra un “giudizio” (vero o simulato).

---

### Modalità C: Il player imita la CPU

**Setup:**

* Il sistema mostra domande (simulate da sessioni precedenti o da un LLM).
* Il player deve **rispondere in modo da sembrare un bot**.
* Un giudice virtuale valuta se è riuscito a “fingere”.

**Pro:**
* Utile per raccogliere nuovi dati (human-as-bot).
* Stimola creatività e strategia.

**Contro:**

* Sempre legato a domande esistenti (oppure generate).

---

## Riepilogo: flessibilità vs. vincolo

| Modalità             | Ruolo del player | Flessibilità domande       | Requisiti                          |
| -------------------- | ---------------- | -------------------------- | ---------------------------------- |
| A - Player è giudice | GIUDICE          | Alta (domande libere)      | Risposte HUMAN sessioni precedenti |
| B - Player è HUMAN   | Risponde         | Media (domande da sistema) | Giudizi e domande passate          |
| C - Player imita CPU | Finta CPU        | Media (domande da sistema) | Giudizi e risposte CPU             |

---

## Soluzioni ibride per aumentare la varietà

Per evitare che il gioco sia vincolato:

1. **Embeddings semantici**:

   * Quando una domanda è nuova, cerca risposte a **domande simili** già in archivio.
   * Ti permette di “adattare” domande nuove a risposte esistenti.

2. **Generazione controllata**:

   * Se non hai una risposta umana nel DB, puoi farla generare da un LLM, etichettandola come HUMAN.
   * Oppure simula un GIUDICE LLM per valutare risposte.
