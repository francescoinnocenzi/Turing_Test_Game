from schemas.api_models import RequestAPI, ResponseAPI
import requests
import json
from utils.emoji import remove_emoji
from fastapi import HTTPException
from schemas.question import QuestionRequest
from database.connection import create_db_connection
from fastapi import HTTPException
import mariadb
from services.transformer import get_model
import torch
from sentence_transformers import util

chat_history: list[dict]= []

# Funzione per ottenere risposta dal LLM
async def get_llm_response(question: str):
    """Funzione che chiama l'API LLM per ottenere una risposta alla domanda"""
    request_data = RequestAPI(question=question)
    try:
        response = ask_with_memory(request_data)
        return response.answer
    except Exception as e:
        print(f"❌ Errore nella chiamata a LLM: {e}")
        return "Mi dispiace, non ho capito la domanda."

def ask_with_memory(request: RequestAPI):

    global chat_history

    chat_history.append({"role": "user", "content": request.question})

    url = "http://ollama:11434/api/chat"

    system_prompt = {
        "role": "system",
        "content": (
            "Rispondi come un essere umano. Stile naturale, diretto e realistico. Chat informale: risposte brevi, massimo  10 parole. Evita frasi inutili o generiche.  Non dire mai che sei un'IA. Se ti chiedono nome, età, luogo o famiglia, inventa risposte credibili. Non dire mai che non sai o rifiutare di rispondere."
        )
    }

    # Mettendo il system prompt all'inizio, il modello LLM lo considera come una direttiva ad alta priorità che deve guidare tutte le sue risposte.
    messages: list = [system_prompt] + chat_history  # prepend il system

    payload = {
        "model": "gemma2:2b-instruct-q2_K", #Versione ottimizzata di gemma2:2b-instruct-q2_K
        "messages": messages,
        "stream": False
    }

    try:

        response = requests.post(url, json=payload)
        response.raise_for_status()
        risposta_api = response.json()
        
        print("Payload inviato a Ollama:\n", json.dumps(payload, indent=2))

        answer = risposta_api["message"]["content"]
        answer = remove_emoji(answer)
        
        chat_history.append({"role": "assistant", "content": answer})

        print(chat_history)

        return ResponseAPI(answer=answer, chat_history=chat_history)
        
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Errore durante richiesta post {e}")


async def trova_simile(request: QuestionRequest):
    model = get_model()  # modello caricato solo alla prima chiamata
    conn = create_db_connection()
    cursor = conn.cursor()
    input_frase = request.text
    soglia_similarità = 0.8

    try:
        # Prendo solo domande di altre sessioni
        cursor.execute("""
            SELECT id, text, embedding
            FROM questions
            WHERE session_id != ?
        """, (request.session_id,))
        frasi_trovate = cursor.fetchall()  # [(id, text, embedding_json), ...]

        if not frasi_trovate:
            risposta_nuova = await get_llm_response(input_frase)
            return {
                "frase_input": input_frase,
                "frase_simile": None,
                "risposta_trovata": risposta_nuova,
                "similarità": 0.0,
                "tipo_risposta": "LLM"
            }

        # Estraggo testi, id e embeddings dal DB
        ids = []
        testi = []
        embeddings_db = []

        for row in frasi_trovate:
            ids.append(row[0])
            testi.append(row[1])
            embeddings_db.append(torch.tensor(json.loads(row[2])))

        embeddings_db = torch.stack(embeddings_db)

        # Embedding input
        embedding_input = model.encode(input_frase, convert_to_tensor=True)

        # Calcolo similarità coseno
        cosine_scores = util.cos_sim(embedding_input, embeddings_db)

        # Trovo frase più simile
        best_idx = cosine_scores.argmax().item()
        best_score = cosine_scores[0][best_idx].item()
        best_sentence = testi[best_idx]
        best_id = ids[best_idx]

        # Trovo risposta umana casuale
        cursor.execute("""
            SELECT text
            FROM answers
            WHERE question_id = ? AND author_type = 'HUMAN'
            ORDER BY RAND()
            LIMIT 1
        """, (best_id,))
        row = cursor.fetchone()
        risposta_trovata = row[0] if row else None

    except mariadb.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

    print(f"BEST SCORE {best_score}")

    if best_score > soglia_similarità and risposta_trovata:
        return {
            "frase_input": input_frase,
            "frase_simile": best_sentence,
            "risposta_trovata": risposta_trovata,
            "similarità": best_score,
            "tipo_risposta": "HUMAN"
        }
    else:
        risposta_nuova = await get_llm_response(input_frase)
        return {
            "frase_input": input_frase,
            "frase_simile": None,
            "risposta_trovata": risposta_nuova,
            "similarità": 0.0,
            "tipo_risposta": "LLM"
        }