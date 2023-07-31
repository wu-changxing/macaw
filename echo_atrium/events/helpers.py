import uuid
from .redis_store import RedisStore
from collections import defaultdict,Counter
redis_store = RedisStore()

def generate_unique_room_id():
    return str(uuid.uuid4())

def get_username_by_sid(sid):
    users = redis_store.load('users')
    for user in users.values():
        if 'sid' in user and user['sid'] == sid:
            return user['username']  # Now 'username' key exists
    return None


def get_sid_by_username(username):
    users = redis_store.load('users')
    for user in users.values():
        if 'username' in user and user['username'] == username:
            return user['sid']
    return None

async def get_room_users(room_id):
    users = redis_store.load('users')
    room_users = {}
    for username, user_data in users.items():
        if user_data.get('room_id') == room_id:  # Use the get() method to avoid KeyError
            room_users[username] = user_data
    return room_users



def calculate_quiz_statistics(room_data):
    # Initialize an empty dictionary to store the statistics
    stats = defaultdict(lambda: {"correct": 0, "incorrect": 0, "item": "", "answer": "", "correct_users": [], "most_wrong_answer": "", "wrong_answers": Counter()})
    scores = room_data['quiz']['scores']

    # Get the quiz history
    history = room_data['quiz']['history']

    # Loop through the history
    for entry in history:
        # Get the question_id, item, answer and whether they were correct
        question_id = entry['question_id']
        item = entry['item']
        answer = entry['answer']
        is_correct = entry['is_correct']
        username = entry['username']
        selected_option = entry['selected_option']  # Assuming selected_option contains the user's answer

        # Set the item and answer if not already set
        if not stats[question_id]["item"]:
            stats[question_id]["item"] = item
        if not stats[question_id]["answer"]:
            stats[question_id]["answer"] = answer

        # Increment the correct or incorrect count based on whether they were correct
        if is_correct:
            stats[question_id]['correct'] += 1
            stats[question_id]['correct_users'].append(username)  # Add the username to the list of correct users
        else:
            stats[question_id]['incorrect'] += 1
            stats[question_id]['wrong_answers'][selected_option] += 1  # Count the frequency of wrong answers

    # Determine the most common wrong answer for each question
    for question_id, data in stats.items():
        if data['wrong_answers']:
            most_common_wrong_answer, _ = data['wrong_answers'].most_common(1)[0]
            data['most_wrong_answer'] = most_common_wrong_answer

    # Convert stats to list for sorting
    stats_list = [{'question_id': k, 'item': v['item'], 'answer': v['answer'], 'correct': v['correct'], 'incorrect': v['incorrect'], 'correct_users': v['correct_users'], 'most_wrong_answer': v['most_wrong_answer']} for k, v in stats.items()]

    # Sort by incorrect in descending order
    stats_list.sort(key=lambda x: x['incorrect'], reverse=True)

    result = {'scores': scores, 'stats': stats_list}
    # Return the final statistics
    return result
