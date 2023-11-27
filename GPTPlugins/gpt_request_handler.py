# gpt_request_handler.py
import openai
import os
import re
from dotenv import load_dotenv

from concurrent.futures import ThreadPoolExecutor,as_completed
# Load the OpenAI API key from the .env file
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def communicate_with_api(string_list, source_locale, target_locale):
    # Prepare the content to be sent to the API
    joined_strings = '|||'.join([f"{i}: {string}" for i, string in enumerate(string_list)])
    num = len(string_list)
    prompt = (
        f"I have several paragraphs from a source text that need to be translated from {source_locale} to {target_locale}. "
        f"pls note that your target language is {target_locale}.\n"
        f"Here are the paragraphs:\n"
        f"{joined_strings}\n"
        "Please note that wherever there's  '<b>' or '|||' in the source text, you should also include it in the translated text.\n "
        f"Also, this translation should be {num} lines from 0 to {num-1} .\n"
    )

    # System message for setting up the role of the model
    system_message = "You are a highly skilled translator. Your task is to translate texts from one language to another."
    
    # The actual interaction with the OpenAI API
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-16k",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3
    )

    # Process the API response
    if response.choices[0].finish_reason == "length":
        # Handle the scenario when the response is cut off due to length
        # This is where you might call another function to handle this, e.g., split the text further
        pass
    else:
        # Process the successful response
        if "|||" in response.choices[0].message.content:
            content = response.choices[0].message.content.strip()
            translated_chunk_raw = content.split("|||")
        else:
            translated_chunk_raw = re.findall(r'\d+: ([^\n]*)', response.choices[0].message.content.strip())
        
        translated_chunk_raw = [text.strip() for text in translated_chunk_raw if text.strip()]
        
        # Clean up the response text
        translated_chunk = [re.sub(r'^[\n]+', '', text) for text in translated_chunk_raw]
        translated_chunk = [re.sub(r'^\d+[.: ]?', '', text) for text in translated_chunk]

        return translated_chunk  # This is the translated content


def handle_translation_requests(chunks, source_locale, target_locale, max_workers=5):
    translated_texts = [None] * len(chunks)  # Initialize with placeholders
    errors = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_index = {
            executor.submit(communicate_with_api, chunk, source_locale, target_locale): index for index, chunk in enumerate(chunks)
        }

        for future in as_completed(future_to_index):
            index = future_to_index[future]  # Get the index of the chunk being processed
            try:
                result = future.result()
                translated_texts[index] = result  # Place the result at the corresponding index
            except Exception as e:
                errors.append(str(e))
                translated_texts[index] = [''] * len(chunks[index])  # Placeholder for failed translation

    return [text for sublist in translated_texts for text in sublist if sublist], errors

if __name__ == "__main__":
    source_locale = "en"
    target_locale = "fr"
    strings_to_translate = ["Hello, world!", "How are you?"]  # This would be a chunk
    chunks = [strings_to_translate]  # For the example, there's only one chunk, but you'd have more.

    translated_content, errors = handle_translation_requests(chunks, source_locale, target_locale)
    print(translated_content)
    if errors:
        print(f"Errors occurred during translation: {errors}")
