# quiz_data.py

from .utils import fetch_words, generate_word_quiz_questions

from .redis_store import RedisStore
from .helpers import get_username_by_sid, get_room_users

redis_store = RedisStore()

async def initialize_quiz_data(level, category, mode, question_timer, room_id):
    if level is not None and category is not None and mode is not None and room_id is not None:
        words = await fetch_words(level, category)
        if words is not None:
            questions = await generate_word_quiz_questions(words)
            redis_store.merge(room_id, {
                'quiz': {
                    'meta': {'level': level, 'category': category, 'mode': mode, 'timer': question_timer},
                    'questions': {i: question for i, question in enumerate(questions)},
                    'scores': {},
                    'current_question_id': 0,
                    'answers': {},
                    'history': []
                }
            })
            return questions
        else:
            return None
    else:
        return None


async def calculate_and_store_answer(sid, room_id, question_id, selected_option):
    username = get_username_by_sid(sid)
    is_correct = False

    if question_id is not None and selected_option is not None and room_id is not None:
        room_data = redis_store.load(room_id)
        question = room_data['quiz']['questions'].get(str(question_id))
        correct_answer = question.get('answer')
        is_correct = selected_option == correct_answer

        if is_correct:
            score = room_data['quiz']['scores'].get(username, 0) + 1
        else:
            score = room_data['quiz']['scores'].get(username, 0) - 2

        answer_detail = {
            'username': username,
            'item':question.get('question'),
            'answer': correct_answer,
            'question_id': question_id,
            'selected_option': selected_option,
            'is_correct': is_correct
        }
        current_history = room_data['quiz'].get('history', [])
        # Append the new answer details
        current_history.append(answer_detail)
        # Update the history in the store
        redis_store.merge(room_id, {'quiz': {'history': current_history}})
        redis_store.merge(room_id, {'quiz': {'scores': {username: score}, 'answers': {username: selected_option}}})

        return is_correct, question, room_data['quiz']['meta']

    else:
        return None, None, None


async def calculate_room_stats(sid, room_id):
    room_data = redis_store.load(room_id)
    quiz = room_data.get('quiz', {})
    current_question_id = quiz.get('current_question_id')
    current_question_stats = quiz.get('questions', {}).get(str(current_question_id), {})

    room_stats = []
    room_users = await get_room_users(room_id)  # fetch room users

    for username in room_users:  # loop through room users
        score = quiz.get('scores', {}).get(username, 0)
        is_answered = username in quiz.get('answers', {}) and quiz.get('answers', {}).get(username) is not None
        is_correct = is_answered and quiz.get('answers', {}).get(username) == current_question_stats.get('answer')
        if is_answered and quiz['meta'].get('mode') == 'single':
            room_stats.append({
                'username': username,
                'score': score,
                'isAnswered': is_answered,
                'isCorrect': is_correct,
            })
        elif quiz['meta'].get('mode') == 'public':
            room_stats.append({
                'username': username,
                'score': score,
                'isAnswered': is_answered,
                'isCorrect': is_correct,
            })
    return room_stats
