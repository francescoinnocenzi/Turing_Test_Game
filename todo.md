# TO-DO LIST

Fra
- rimuovi emoji da domande e md o asterischi da domande/risposta
- Blocca input bottone player A o B judge dopo fine game
- Player A e B frontend modalità giudice 
- CSS
- Rivedi frontend.py alcuni endpoint sono inutili
- Invio domanda multi con Enter
- Aggiungi cartella olloma_models vedi da esnoero finale
- Manca giudizio modalita multi
- Quando finisce la partita blocca input / bottoni per dare giudizio A o B
- Judge input bloccato quando sta da solo
- Alcuni pydantic sono inutili levali, spesso quelli di reponse

Luca
- Modalità SINGLE HUMAN in cui le domande le prendi dalle sessioni passate e le riposte BOT pure
- cartelle
- mette appsoto il db foreign key

```python
 # in realtà id lo recupera qua come quello più recente non vabbene
    if not question_id:
        conn = create_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id FROM questions 
            WHERE room_name = ? 
            ORDER BY created_at DESC 
            LIMIT 1
        """, (room_name,))
        last_q = cur.fetchone()
        cur.close(); conn.close()
        if last_q:
            question_id = last_q[0]