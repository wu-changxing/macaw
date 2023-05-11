from wagtail_localize.machine_translators.base import BaseMachineTranslator
import openai
import os
from wagtail_localize.strings import StringValue
import re
from dotenv import load_dotenv, set_key

class ChatGPTTranslator(BaseMachineTranslator):
    display_name = "ChatGpt"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        load_dotenv()
        openai.api_key = os.getenv("OPENAI_API_KEY")

    def update_total_cost(self, cost):
        current_cost = float(os.getenv("TOTAL_COST", 0))
        new_cost = current_cost + cost
        dotenv_path = '.env'
        set_key(dotenv_path, "TOTAL_COST", str(new_cost))

    def get_chunked_strings(self, strings, num_chunks):
        strings_list = [string.data for string in strings]
        chunk_size = len(strings_list) // num_chunks
        chunks = [strings_list[i:i + chunk_size] for i in range(0, len(strings_list), chunk_size)]
        if len(chunks) > num_chunks:
            chunks[-2].extend(chunks[-1])
            chunks.pop()
        return chunks

    def translate(self, source_locale, target_locale, strings):
        string_list = [string.data for string in strings]
        concatenated_strings = ' '.join(string_list)
        total_tokens = len(concatenated_strings.split(' '))
        num_chunks = max(1, (total_tokens // 4000) + 1)
        chunks = self.get_chunked_strings(strings, num_chunks)

        translated_text = []

        for chunk in chunks:
            string_list = [string for string in chunk]
            string_list_joined = '\n'.join([f"{i}: {string}" for i, string in enumerate(string_list)])

            prompt = f"Please translate the following strings from {source_locale} to {target_locale}:\n{string_list_joined}\nIf you are unable to translate a string, please provide the original text as the translation. Return the translations line by line in the same order."

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": f"You are a great translation assistant. Your input language is {source_locale} and your output language is {target_locale}."},
                    {"role": "user", "content": prompt},
                ]
            )

            usage = response["usage"]["total_tokens"]
            cost = usage / 1000 * 0.002
            self.update_total_cost(cost)
            print(f"Updated total cost = ${os.getenv('TOTAL_COST')}")
            translated_chunk_raw = response['choices'][0]['message']['content'].strip().split('\n')
            translated_chunk = [re.sub(r'^\d+: ', '', text) for text in translated_chunk_raw]
            translated_text.extend(translated_chunk)

        result = {
            original_string: StringValue.from_plaintext(translated)
            for original_string, translated in zip(strings, translated_text)
        }

        return result

    def can_translate(self, source_locale, target_locale):
        return source_locale.language_code != target_locale.language_code
