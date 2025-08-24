## Tabelle necessarie

### 1. `users`

| Campo          | Tipo       | Note      |
| -------------- | ---------- | --------- |
| id             | INTEGER PK |           |
| username       | TEXT       | Unico     |
| password\_hash | TEXT       | Sicurezza |
| created\_at    | TIMESTAMP  |           |

---

### 2. `sessions`

| Campo       | Tipo       | Note        |
| ----------- | ---------- | ----------- |
| id          | INTEGER PK |             |
| room\_name  | TEXT       | es. "room1" |
| created\_at | TIMESTAMP  |             |

---

### 3. `session_participants`

| Campo       | Tipo       | Note                             |
| ----------- | ---------- | -------------------------------- |
| id          | INTEGER PK |                                  |
| session\_id | INTEGER FK | → sessions                       |
| user\_id    | INTEGER FK | → users                          |
| role        | TEXT       | ("JUDGE", "HUMAN", "CPU")        |
| is\_real    | BOOLEAN    | true = player reale, false = CPU |

---

### 4. `questions`

| Campo       | Tipo       | Note                             |
| ----------- | ---------- | -------------------------------- |
| id          | INTEGER PK |                                  |
| session\_id | INTEGER FK | → sessions                       |
| author\_id  | INTEGER FK | → users (il giudice umano o CPU) |
| text        | TEXT       | Contenuto della domanda          |
| created\_at | TIMESTAMP  |                                  |

---

### 5. `answers`

| Campo        | Tipo       | Note                       |
| ------------ | ---------- | -------------------------- |
| id           | INTEGER PK |                            |
| question\_id | INTEGER FK | → questions                |
| author\_id   | INTEGER FK | → users (chi ha risposto)  |
| text         | TEXT       | Risposta                   |
| is\_real     | BOOLEAN    | true = utente, false = CPU |
| created\_at  | TIMESTAMP  |                            |

---

### 6. `judgements`

| Campo         | Tipo       | Note                                   |
| ------------- | ---------- | -------------------------------------- |
| id            | INTEGER PK |                                        |
| session\_id   | INTEGER FK | → sessions                             |
| judge\_id     | INTEGER FK | → users (giudice umano o CPU)          |
| guessed\_user | INTEGER FK | → users (secondo il giudice era HUMAN) |
| verdict\_time | TIMESTAMP  |                                        |

