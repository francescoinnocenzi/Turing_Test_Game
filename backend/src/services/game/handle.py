from schemas.question import QuestionRequest
from schemas.answer import AnswerRequest
from schemas.judgment import JudgmentRequest
from schemas.judgment import JudgmentRequest
from services.game.questions import create_question
from services.game.answers import create_answer
from services.game.judgment import create_judgment
from services.llm.generate_answer import get_llm_response
from services.llm.generate_answer import trova_simile
from services.instances.manager import manager
from services.game.check import check_all_answered
from services.game.scores import handle_scores
import services.state as state
from typing import Dict, Any
import random
from services.instances.manager import ConnectionManager

async def assign_and_send_positions(room_name: str, manager: ConnectionManager) -> Dict[str, Dict[str, str]]:
    """
    Assegna posizioni casuali (left/right) ai giocatori nella stanza.
    Se le posizioni sono già state assegnate, le restituisce senza reinviare.

    Args
        room_name (str): Nome della stanza.
        manager (ConnectionManager): Oggetto manager che gestisce l'invio dei messaggi ai client.

    Returns
        Dizionario con le posizioni assegnate, es.:
            {
                "left": {"type": "HUMAN"},
                "right": {"type": "BOT"}
            }
    """
    if room_name in state.room_positions:
        # Posizioni già assegnate, non reinvia
        return state.room_positions[room_name]

    # Definisci i giocatori
    players = [
        {"type": "HUMAN"},
        {"type": "BOT"}
    ]

    # Mischia l'ordine
    random.shuffle(players)

    # Assegna posizioni
    state.room_positions[room_name] = {
        "left": players[0],
        "right": players[1]
    }

    # Invia al judge
    await manager.send_positions_to_judge(room_name, state.room_positions[room_name])

    print(f"Assigned positions in {room_name}: {state.room_positions[room_name]}")
    return state.room_positions[room_name]


#Gestione della domanda in arrivo (singleplayer)
async def handle_question(room_name: str, role: str, message: Dict[str, str], mode: str, session_id: int, user_id: int) -> None:
    """
    Salva la domanda, assegna posizioni ai giocatori, invia la domanda ai client,
    genera risposte dei bot e verifica se tutti hanno risposto.

    Args
        room_name (str): Nome della stanza.
        role (str): Ruolo del mittente ("HUMAN" o "JUDGE").
        message (Dict[str, str]): Messaggio contenente il testo della domanda.
        mode (str): Modalità di gioco ("single" o "multi").
        session_id (int): ID della sessione corrente.
        user_id (int): ID dell'utente che invia la domanda.

    Returns
        None
    """
    text = message.get("text")

    print(f"Messaggio arrivato da {role}: {text}")

    # Salva domanda
    q_req = QuestionRequest(
        text=text,
        room_name=room_name,
        author_user_id=user_id,
        session_id=session_id,
        author_type="HUMAN"
    )
    saved_q = create_question(q_req)

    print(f"Current room positions: {state.room_positions}")
    # Assegna e invia posizioni solo se non già fatto
    await assign_and_send_positions(room_name, manager)

    # Invia domanda a players (caso multiplayer)
    await manager.send_question_to_players(text, room_name, saved_q.id)
    print(f"Question sent to players in room {room_name}")

    # BOT 1 (LLM)
    bot1_resp = await get_llm_response(text)
    #Salva risposta bot 
    create_answer(AnswerRequest(
        question_id=saved_q.id,
        session_id=session_id,
        text=bot1_resp,
        author_user_id=None,
        author_type="BOT",
        room_name=room_name
    ))
    await manager.send_answer_to_judge(bot1_resp, room_name, "BOT")
    print(f" BOT-LLM answer sent: {bot1_resp}")  

    # Ho ricevuto una domanda da giudice (se sto in single, genero altra riposta HUMAN)
    if mode == "single":
        # BOT 2 (retrieval o fallback LLM)
        bot2_data = await trova_simile(q_req)
        bot2_resp = bot2_data.risposta_trovata
        
        create_answer(AnswerRequest(
            question_id=saved_q.id,
            session_id=session_id,
            text=bot2_resp,
            author_user_id=None,
            author_type="BOT_AS_HUMAN" if bot2_data.tipo_risposta == "LLM" else "HUMAN",
            room_name=room_name
        ))
        await manager.send_answer_to_judge(bot2_resp, room_name, "HUMAN") #metto 1 perche risponde al posto di HUMAN
        print(f" BOT-Retrieval answer sent: {bot2_resp}")  # <-- log

    await check_all_answered(saved_q.id, room_name, session_id=session_id, role=role, mode=mode, user_id=user_id)

#Gestione della risposta inviata singleplayer
async def handle_answer(room_name: str, role: str, message: Dict[str, Any], mode: str, session_id: int, user_id: int) -> None:
    """
    Gestisce l'arrivo di una risposta da un player.

    Salva la risposta nel DB e notifica il giudice.
    Controlla se tutti hanno risposto tramite check_all_answered.

    Args
        room_name (str): Nome della stanza.
        role (str): Ruolo del mittente ("HUMAN" o "JUDGE").
        message (Dict[str, Any]): Messaggio contenente text e question_id.
        mode (str): Modalità di gioco ("single" o "multi").
        session_id (int): ID della sessione corrente.
        user_id (int): ID dell'utente che invia la risposta.

    Returns
        None
    """
    print("RISPOSTA ARRIVATA:",{"role": role, "message": message, "mode": mode})
    print(f"QUESTION_ID in handle_answer: {message.get('question_id')}") # stampa None
    text = message.get("text")
    question_id = message.get("question_id")

    print(f" Risposta da {role}: {text} mode : {mode}")

    await manager.send_answer_to_judge(text, room_name, "HUMAN")

    if question_id:
        create_answer(AnswerRequest(
            question_id=question_id,
            session_id=session_id,
            text=text,
            author_user_id=user_id,
            author_type="HUMAN",
            room_name=room_name
        ))
    
    # Usa la funzione centralizzata per verificare se tutti hanno risposto, perché giudice è LLM e devo capire se posso generare la prossima domanda
    await check_all_answered(question_id, room_name, session_id=session_id, role=role, mode=mode, user_id=user_id)

async def handle_message(msg_type: str, room_name: str, role: str, message: Dict[str, Any], mode: str, session_id: int, user_id: int, manager: ConnectionManager):
    """
    Smista il messaggio al corretto handler in base al tipo.

    Args
        msg_type (str): Tipo del messaggio ("question", "answer", "judge_choice").
        room_name (str): Nome della stanza.
        role (str): Ruolo del mittente.
        message (Dict[str, Any]): Messaggio ricevuto.
        mode (str): Modalità di gioco.
        session_id (int): ID della sessione.
        user_id (int): ID dell'utente.
        manager (ConnectionManager): Manager per l'invio dei messaggi.

    Returns
        None
    """
    handlers = {
        "question": handle_question,
        "answer": handle_answer,
        "judge_choice": handle_judge_choice,
    }

    # Controllo che msg_type ricevuto rientri nei messaggi gestiti
    if msg_type in handlers:
        handler = handlers[msg_type]
        
        if msg_type == "judge_choice":
            await handler(room_name=room_name, message=message, session_id=session_id, user_id=user_id, manager=manager, role=role, mode=mode)
        else:
            await handler(room_name=room_name, message=message, session_id=session_id, user_id=user_id, role=role, mode=mode)
    else:
        print(f"Messaggio sconosciuto: {msg_type}")
from typing import Any, Dict

async def handle_judge_choice(room_name: str, message: Dict[str, Any], session_id: int, user_id: int, manager: ConnectionManager, role: str, mode: str) -> None:
    """
    Gestisce la scelta del giudice e aggiorna i punteggi.

    Args
        room_name (str): Nome della stanza.
        message (Dict[str, Any]): Messaggio con la scelta del giudice.
        session_id (int): ID della sessione.
        user_id (int): ID del giudice.
        manager (ConnectionManager): Manager per invio messaggi.
        role (str): Ruolo del giudice.
        mode (str): Modalità di gioco.

    Returns
        None
    """
    chosen_player_human = message.get("chosen_player_human")  # "A" o "B"
    print("📥 Giudizio ricevuto:", chosen_player_human)

    judgment_req = JudgmentRequest(
        session_id=session_id,
        judge_id=user_id,
        chosen_player_human=chosen_player_human
    )
    result_judgment = create_judgment(judgment_req)
    judge_choice = result_judgment.chosen_player_human

    # Recupera le posizioni assegnate
    positions = state.room_positions.get(room_name)
    if not positions:
        print("ERRORE: posizioni non trovate per la room")
        return
    # Se GIUDICE sceglie "A" prendi il tipo del giocatore a sinistra, se sceglie "B" prendi il tipo del giocatore a destra
    chosen_type = positions["left"]["type"] if judge_choice == "A" else positions["right"]["type"]
    # Se il tipo scelto è "HUMAN", ha indovinato
    correct_answer = (chosen_type == "HUMAN")

    print(f"SCELTA FRONTEND: {judge_choice} → {chosen_type}")

    if correct_answer:
        handle_scores(user_id, session_id, mode, role=role, win=True)
        await manager.send_judgment_to_all("GIUDICE ha VINTO", room_name)
    else:
        handle_scores(user_id, session_id, mode, role=role, win=False)
        await manager.send_judgment_to_all("GIUDICE ha PERSO", room_name)
