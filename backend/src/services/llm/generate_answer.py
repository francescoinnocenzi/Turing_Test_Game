from schemas.api_models import RequestAPI, ResponseAPI
import requests
import json
from utils.clean_text import clean_text
from fastapi import HTTPException
from schemas.question import QuestionRequest
from database.connection import create_db_connection
from fastapi import HTTPException
import mariadb
from services.llm.transformer import get_model
import torch
from sentence_transformers import util
import services.state as state
from schemas.api_models import SimilarityResponse

state.chat_history = [] # list[dict]

# Funzione per ottenere risposta dal LLM
async def get_llm_response(question: str) -> str:
    """
    Ottiene una risposta dal modello LLM data una domanda.

    Args
        question (str): La domanda da inviare al modello.

    Returns
        str: La risposta generata dal modello.

    Notes
        Se si verifica un errore, restituisce una risposta di fallback.
    """
    
    request_data = RequestAPI(question=question)
    try:
        response = ask_with_memory(request_data)
        return response.answer
    except Exception as e:
        print(f"❌ Errore nella chiamata a LLM: {e}")
        return "Mi dispiace, non ho capito la domanda."

def ask_with_memory(request: RequestAPI) -> ResponseAPI:
    """
    Gestisce la chat con il modello LLM mantenendo la cronologia delle conversazioni.

    Args
        request (RequestAPI): Oggetto contenente la domanda da inviare al modello.

    Returns
        ResponseAPI: Oggetto contenente la risposta e la chat history aggiornata.

    Raises
        HTTPException: Se la chiamata all'API del modello fallisce.
    """

    state.chat_history.append({"role": "user", "content": request.question})

    url = "http://ollama:11434/api/chat"

    system_prompt = {
        "role": "system",
        "content": (
            "Rispondi come un essere umano. Stile naturale, diretto e realistico. Chat informale: risposte brevi, massimo  10 parole. Evita frasi inutili o generiche.  Non dire mai che sei un'IA. Se ti chiedono nome, età, luogo o famiglia, inventa risposte credibili. Non dire mai che non sai o rifiutare di rispondere."
        )
    }

    # Mettendo il system prompt all'inizio, il modello LLM lo considera come una direttiva ad alta priorità che deve guidare tutte le sue risposte.
    messages: list = [system_prompt] + state.chat_history  # prepend il system

    payload = {
        #gemma2:2b-instruct-q2_K
        #gemma3:4b
        "model": "gemma2:2b-instruct-q2_K", #Versione ottimizzata di gemma3:4b
        "messages": messages,
        "stream": False
    }

    try:

        response = requests.post(url, json=payload)
        response.raise_for_status()
        risposta_api = response.json()
        
        print("Payload inviato a Ollama:\n", json.dumps(payload, indent=2))

        answer = risposta_api["message"]["content"]
        answer = clean_text(answer)
        
        state.chat_history.append({"role": "assistant", "content": answer})

        print(state.chat_history)

        return ResponseAPI(answer=answer, chat_history=state.chat_history)
        
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Errore durante richiesta post {e}")


async def trova_simile(request: QuestionRequest) -> SimilarityResponse:
    """
    Trova la risposta più simile ad una domanda già presente nel database,
    altrimenti genera una nuova risposta con l'LLM.

    Args
        request (QuestionRequest): Oggetto contenente la nuova domanda e l'ID della sessione.

    Returns
        SimilarityResponse: Risultato con la frase più simile (se trovata),
                            la risposta associata (umana o LLM),
                            il punteggio di similarità e il tipo di risposta.

    Raises
        HTTPException: Se si verifica un errore di database.
    """
    model = get_model()  # modello caricato solo alla prima chiamata
    conn = create_db_connection()
    cursor = conn.cursor()

    input_frase = request.text
    soglia_similarità = 0.8

    try:
        # Prendo solo domande di sessioni precedenti
        cursor.execute("""
            SELECT id, text, embedding
            FROM questions
            WHERE session_id != ?
        """, (request.session_id,))
        frasi_trovate = cursor.fetchall()  # [(id, text, embedding_json), ...]

        # Se non ha trovato domande di sessioni precedenti nel db
        if not frasi_trovate:
            # La risposta viene generata dal modello LLM
            risposta_nuova = await get_llm_response(input_frase)
            response = SimilarityResponse(
                frase_input=input_frase,
                frase_simile=None,
                risposta_trovata=risposta_nuova,
                similarita=0.0,
                tipo_risposta="LLM"
            )
            
            return response

        # Estraggo testi, id e embeddings dal DB
        ids = []
        testi = []
        embeddings_db = []

        for row in frasi_trovate:
            ids.append(row[0])
            testi.append(row[1])
            embeddings_db.append(torch.tensor(json.loads(row[2]))) # deserializzo da JSON in tensore che utilizza pytorch

        embeddings_db = torch.stack(embeddings_db) 

        # Embedding input in ingresso
        embedding_input = model.encode(input_frase, convert_to_tensor=True)

        # Calcolo similarità coseno tra embedding_input e embeddings_db
        cosine_scores = util.cos_sim(embedding_input, embeddings_db)

        # Trovo domanda più simile
        best_idx = cosine_scores.argmax().item() # Indice del valore massimo
        best_score = cosine_scores[0][best_idx].item() # Punteggio di similarità
        best_sentence = testi[best_idx] # Testo della domanda più simile
        best_id = ids[best_idx] # ID della domanda più simile

        # Trovo risposta umana casuale relativa alla domanda simile
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
        response = SimilarityResponse(
            frase_input=input_frase,
            frase_simile=best_sentence,
            risposta_trovata=risposta_trovata,
            similarita=best_score,
            tipo_risposta="HUMAN"
        )

        return response
    else:
        risposta_nuova = await get_llm_response(input_frase)
        
        response = SimilarityResponse(
            frase_input=input_frase,
            frase_simile=None,
            risposta_trovata=risposta_nuova,
            similarita=0.0,
            tipo_risposta="LLM"
        )

        return response