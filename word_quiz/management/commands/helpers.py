# word_quiz/management/commands/helpers.py:
def get_category(file_name):
    if 'IELTS' in file_name:
        category = 'IELTS'
    elif 'TOEFL' in file_name:
        category = 'TOEFL'
    elif 'GRE' in file_name:
        category = 'GRE'
    elif 'SAT' in file_name:
        category = 'SAT'
    elif 'GMAT' in file_name:
        category = 'GMAT'
    elif 'CET4' in file_name:
        category = 'CET4'
    elif 'CET6' in file_name:
        category = 'CET6'
    elif 'KET' in file_name:
        category = 'KET'
    elif 'PET' in file_name:
        category = 'PET'
    elif 'FCE' in file_name:
        category = 'FCE'
    elif 'PTE' in file_name:
        category = 'PTE'
    else:
        category = 'Other'
    return category