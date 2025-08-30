
from database.connection import create_db_connection
import requests

async def get_llm_judgment(session_id: int):
    """Fa decidere all'LLM chi è HUMAN e chi è BOT basandosi sulle risposte della sessione"""
    try:
        # Recupera tutte le domande e risposte per questa sessione
        conn = create_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT q.text as question, a.text as answer, a.author_type, a.author_user_id
            FROM questions q
            JOIN answers a ON q.id = a.question_id
            WHERE q.session_id = ? AND a.session_id = ?
            ORDER BY q.created_at, a.author_type
        """, (session_id, session_id))
        
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if not results:
            return {"error": f"Nessuna risposta trovata per la sessione {session_id}"}
        
        # Organizza le risposte per player
        human_responses = []
        bot_responses = []
        
        for row in results:
            question, answer, author_type, author_user_id = row
            
            if author_type == "HUMAN":
                human_responses.append(f"Q: {question}\nA: {answer}")
            elif author_type == "BOT":
                bot_responses.append(f"Q: {question}\nA: {answer}")
        
        # Randomizza SOLO i nomi, non i dati
        import random
        player_a_name = "Player A"
        player_b_name = "Player B"

        players_data = [
            (human_responses, "HUMAN"),
            (bot_responses, "BOT")  
        ]
        random.shuffle(players_data)

        # Ora assegna in modo chiaro
        player_a_responses, player_a_real_type = players_data[0]
        player_b_responses, player_b_real_type = players_data[1]
        
        # Prepara il prompt per l'LLM giudice
        judgment_prompt = {
            "role": "system",
            "content": (
                "Sei un giudice in un Turing Test. "
                "Analizza le risposte dei due player e decidi chi è UMANO e chi è IA/BOT. "
                "Concentrati su: naturalezza, errori umani, stile di scrittura, coerenza. "
                "Gli umani spesso fanno errori di battitura, sono meno precisi, più colloquiali. "
                "Le IA sono spesso più precise, formali, evitano errori. "
                "Rispondi SOLO con: 'Player A è UMANO' oppure 'Player B è UMANO'."
            )
        }
        
        conversation_data = {
            "role": "user", 
            "content": (
                f"{player_a_name} (risposte):\n" + "\n\n".join(player_a_responses) + 
                "\n\n--- SEPARATORE ---\n\n" +
                f"{player_b_name}(risposte):\n" + "\n\n".join(player_b_responses) +
                "\n\n Rispondi SOLO con 'Player A è UMANO' o 'Player B è UMANO'."
            )
        }

        print(conversation_data)

        messages = [judgment_prompt, conversation_data]
        
        # Chiama l'LLM per il giudizio
        url = "http://ollama:11434/api/chat"
        payload = {
            "model": "gemma2:2b-instruct-q2_K",
            "messages": messages,
            "stream": False
        }
        
        response = requests.post(url, json=payload)
        response.raise_for_status()
        risposta_api = response.json()
        
        llm_judgment = risposta_api["message"]["content"].strip()

        llm_choice = None

        if "Player A è UMANO" in llm_judgment:
            llm_choice = 'A'
        elif "Player B è UMANO" in llm_judgment:
            llm_choice = 'B'

        print(player_b_real_type, player_a_real_type)
        
        # All' inizio imposto variabile su falso, se non ha indovinato LLM rimane falso, altrimenti cambia valore in vero
        correct_answer = False

        if llm_choice == 'A' and player_a_real_type == "HUMAN":
            correct_answer = True

        elif llm_choice == 'B' and player_b_real_type == "HUMAN":
            correct_answer = True

        return {
            "correct_answer": correct_answer,
            "llm_choice": llm_choice,
            "judgment": llm_judgment,
            "session_id": session_id,
            "human_responses": len(human_responses),
            "bot_responses": len(bot_responses),
            "correct_guess": ("GIUDICE ha VINTO" if correct_answer else "GIUDICE ha PERSO"),
            "human_result": ("HUMAN ha VINTO" if not correct_answer else "HUMAN ha PERSO")
        }
        
    except Exception as e:
        print(f"Errore nel giudizio LLM: {e}")
        return {"error": str(e)}