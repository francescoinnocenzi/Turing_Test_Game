from schemas.question import QuestionRequest
from schemas.answer import AnswerRequest
from services.game.answers import create_answer
from services.game.questions import create_question
from services.instances.manager import manager
from fastapi import HTTPException
import requests
import random
from services.llm.generate_answer import get_llm_response

previous_questions : list[str] = []

# Funzione per ottenere domanda dal LLM
async def get_llm_question():
    """Funzione che chiama l'API LLM per ottenere una domanda"""
    try:
        response = create_question_llm()
        print(f"RESPONSE {response}")
        return response.get("question")
    except Exception as e:
        print(f"❌ Errore nella chiamata a LLM: {e}")
        return "Errore nella generazione domanda."
    
def create_question_llm():

    url = "http://ollama:11434/api/chat"

    themes = ["cultura", "calcio", "sport", "cucina", "moda", "abitudini", "emozioni", "passioni"]
    theme = random.choice(themes)

    question_prompt = {
        "role": "system",
        "content": (
            "Crea una sola domanda breve (max 7 parole). "
            "Naturale e colloquiale, stile chat. "
            "Solo la domanda, niente emoji. "
            "Evita riferimenti a personaggi famosi, politica o attualità. "
            "Tema: {theme}. "
            "Non ripetere domande già fatte."
        )
    }

    messages = [
        question_prompt,
        {"role": "user", "content": f"Genera una domanda sul tema: {theme}"}
    ]

    global previous_questions

    for question in previous_questions:
        messages.append({
            "role": "user",
            "content": f"Domanda già fatta: {question}"
        })

    print(messages)

    payload = {
        "model": "gemma2:2b-instruct-q2_K",
        "messages": messages,
        "stream": False
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        risposta_api = response.json()
        
        # print("Payload inviato a Ollama:\n", json.dumps(payload, indent=2))

        question = risposta_api["message"]["content"]
        previous_questions.append(question)

        return {"question": question} 
           
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Errore durante richiesta post {e}")

async def auto_generate_next_question(room_name: str, session_id: int):
    """Genera automaticamente la prossima domanda dopo che tutti hanno risposto"""
    try:
        import asyncio
        
        # Piccolo delay per dare tempo all'utente di leggere le risposte
        await asyncio.sleep(5)
        
        # Genera nuova domanda
        print("🎯 Auto-generando prossima domanda...")
        next_question = await get_llm_question()
        
        if next_question:
            print(f"📝 Nuova domanda: {next_question}")
                        
            # Salva nel database
            question_request = QuestionRequest(
                text=next_question,
                room_name=room_name,
                author_user_id=None,
                session_id=session_id,
                author_type="BOT"
            )
            saved_question = create_question(question_request)
                        
            # Invia la domanda ai player
            await manager.send_question_to_players(next_question, room_name, saved_question.id)

            
            print(f"✅ Domanda salvata con ID: {saved_question.id}")
            
            # Genera risposta automatica del bot
            print("🤖 Generando risposta automatica del bot...")
            bot_response = await get_llm_response(next_question)
            
            # Salva la risposta del bot
            bot_answer_request = AnswerRequest(
                question_id=saved_question.id,
                session_id=session_id,
                text=bot_response,
                author_user_id=None,
                author_type="BOT",
                room_name=room_name
            )
            create_answer(bot_answer_request)
            
            print(f"🤖 Risposta bot salvata: {bot_response}")

            # await manager.send_message_to_all("Puoi rispondere alla nuova domanda!", "question_new", room_name)

            return next_question
            
        else:
            print("❌ Errore nella generazione della domanda automatica")

            return None
            
    except Exception as e:
        print(f"❌ Errore in auto_generate_next_question: {e}")
