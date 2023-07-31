# quiz_events.py

from . import sio
from .helpers import get_username_by_sid, get_room_users, get_sid_by_username, calculate_quiz_statistics
from .redis_store import RedisStore
from .quiz_data import calculate_and_store_answer

redis_store = RedisStore()

async def emit_first_question(sid, room_id, question_timer, questions, mode):
    first_question = questions['0'].copy()
    first_question.pop('answer')
    first_question['id'] = 0
    first_question['timer'] = question_timer
    if mode == 'single':
        await sio.emit('question', first_question, room=sid)
    elif mode == 'public':
        await sio.emit('showQuiz', room=room_id, skip_sid=sid)
        await sio.emit('question', first_question, room=room_id)
    await sio.emit('questionView', room=room_id)


async def emit_to_all_room_users(first_question, room_id):
    room_users = await get_room_users(room_id)
    for username in room_users:
        user_sid = get_sid_by_username(username)
        if user_sid:
            await sio.emit('question', first_question, room=user_sid)
            redis_store.merge(room_id, {'quiz': {'answers': {username: None}}})

async def emit_answer_and_scores(room_id, sid, is_correct, question, selected_option, question_id, quiz_meta):
    await sio.emit('checkAnswer', {'isCorrect': is_correct, 'answer': question}, room=sid)
    sio.logger.info(f"User {get_username_by_sid(sid)} submitted answer {selected_option} for question_id {question_id}")

    question_timer = quiz_meta.get('timer', 10)
    await sio.emit('receivedAnswer', selected_option, room=room_id)
    room_data = redis_store.load(room_id)
    if all(answer is not None for answer in room_data['quiz']['answers'].values()):
        scores = room_data['quiz']['scores']
        await sio.emit('scores', scores, room=room_id if quiz_meta.get('mode') == 'public' else sid)


async def emit_next_question(sid, room_id, question_timer):
    room_data = redis_store.load(room_id)
    current_question_id = room_data['quiz']['current_question_id']
    next_question_id = current_question_id + 1
    next_question = room_data['quiz']['questions'].get(str(next_question_id))

    if next_question is None:
        await end_quiz(room_id)
        return False

    next_question_copy = next_question.copy()
    next_question_copy.pop('answer')
    next_question_copy['id'] = next_question_id
    next_question_copy['timer'] = question_timer

    room_users = await get_room_users(room_id)
    for username in room_users:
        user_sid = get_sid_by_username(username)
        if user_sid:
            redis_store.merge(room_id, {'quiz': {'answers': {username: None}, 'current_question_id': next_question_id}})
    await sio.emit('question', next_question_copy, room=room_id)
    await sio.emit('questionView', room=room_id)
    scores = room_data['quiz']['scores']
    await sio.emit('scores', scores, room=room_id)
    return True

async def end_quiz(room_id):
    room_data = redis_store.load(room_id)
    result = calculate_quiz_statistics(room_data)
    await sio.emit('endQuiz', result, room=room_id)
    # Clear quiz data for room in Redis
    room_data.pop('quiz', None)
    redis_store.save(room_id, room_data)
    sio.logger.info(f"Quiz ended for room {room_id}")
