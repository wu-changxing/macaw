# quiz_socket.py

from . import sio
from .helpers import get_username_by_sid
from .redis_store import RedisStore
from .quiz_data import initialize_quiz_data, calculate_and_store_answer, calculate_room_stats
from .quiz_events import emit_first_question, emit_answer_and_scores, emit_next_question

redis_store = RedisStore()


@sio.event
async def initQuestions(sid, data):
    level = data.get('level')
    category = data.get('category')
    mode = data.get('mode')
    question_timer = data.get('timer', 10)
    room_id = data.get('room_id')

    if level is None or category is None or mode is None or room_id is None:
        sio.logger.error("No level, category or mode found in initQuestions event data")
        return

    if not await initialize_quiz_data(level, category, mode, question_timer, room_id):
        return
    room_data = redis_store.load(room_id)
    questions = room_data['quiz']['questions']
    await emit_first_question(sid, room_id, question_timer, questions, mode)


@sio.event
async def submitAnswer(sid, data):
    room_id = data.get('room_id')
    question_id = data.get('questionId')
    selected_option = data.get('selectedOption')

    if room_id and question_id is not None and selected_option is not None:
        is_correct, question, quiz_meta = await calculate_and_store_answer(sid, room_id, question_id, selected_option)
        await emit_answer_and_scores(room_id, sid, is_correct, question, selected_option, question_id, quiz_meta)
    else:
        sio.logger.error(f"No room_id, questionId or selectedOption found in submitAnswer event data")


@sio.event
async def nextQuestion(sid, data):
    room_id = data.get('room_id')
    if room_id is not None:
        await emit_next_question(sid, room_id)
    else:
        sio.logger.error(f"No room_id found in nextQuestion event data")


@sio.event
async def getStats(sid, data):
    room_id = data.get('room_id')
    if room_id is not None:
        room_stats = await calculate_room_stats(sid, room_id)
        await sio.emit('stats', room_stats, room=sid)
    else:
        sio.logger.error(f"No room_id found in getStats event data")


@sio.event
async def joinQuiz(sid, data):
    room_id = data.get('room_id')
    room_data = redis_store.load(room_id)
    current_question_id = room_data['quiz']['current_question_id']
    username = get_username_by_sid(sid)
    next_question = room_data['quiz']['questions'].get(str(current_question_id))
    next_question_copy = next_question.copy()
    next_question_copy.pop('answer')
    next_question_copy['id'] = current_question_id
    if room_id is not None and username is not None:
        await sio.emit('room_chat_msg', {'user': username, 'message': f'{username} joined the quiz'}, room=room_id,
                       skip_sid=sid)
        await sio.emit('question', next_question_copy, room=sid)
        sio.logger.info(f"User {username} joined quiz room {room_id}")
    else:
        sio.logger.error("No room_id or username found in joinQuiz event data")
