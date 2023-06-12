import string
from retrying import retry


from wagtail_localize.machine_translators.base import BaseMachineTranslator
import openai
import os
from wagtail_localize.strings import StringValue
import re
from dotenv import load_dotenv, set_key
import tiktoken
def num_tokens_from_messages(messages, model="gpt-3.5-turbo-0301"):
    """Returns the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        print("Warning: model not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")
    if model == "gpt-3.5-turbo":
        print("Warning: gpt-3.5-turbo may change over time. Returning num tokens assuming gpt-3.5-turbo-0301.")
        return num_tokens_from_messages(messages, model="gpt-3.5-turbo-0301")
    elif model == "gpt-4":
        print("Warning: gpt-4 may change over time. Returning num tokens assuming gpt-4-0314.")
        return num_tokens_from_messages(messages, model="gpt-4-0314")
    elif model == "gpt-3.5-turbo-0301":
        tokens_per_message = 4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
        tokens_per_name = -1  # if there's a name, the role is omitted
    elif model == "gpt-4-0314":
        tokens_per_message = 3
        tokens_per_name = 1
    else:
        raise NotImplementedError(f"""num_tokens_from_messages() is not implemented for model {model}. See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens.""")
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 43  # every reply is primed with <|start|>assistant<|message|>
    return num_tokens
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

    def get_tokens_num(self, target):
        messages = [{"role": "user", "content": target}]
        token_count = num_tokens_from_messages(messages)
        print(f"Token count: {token_count}")
        return token_count
    def split_and_translate(self, string_list, source_locale, target_locale):
        if len(string_list) == 1:
            raise RuntimeError("The string is too large to translate in one API call.")

        half = len(string_list) // 2
        first_half = string_list[:half]
        second_half = string_list[half:]

        translated_text = []

        for sub_list in [first_half, second_half]:
            translated_text += self.translate_chunk(sub_list, source_locale, target_locale)

        return translated_text

    @retry(stop_max_attempt_number=3, wait_exponential_multiplier=1000, wait_exponential_max=10000)
    def translate_chunk(self, string_list, source_locale, target_locale):
        joined_strings = '\n'.join([f"{i} {string}" for i, string in enumerate(string_list)])
        prompt = (
            f"the source paragraphs from the source article or poem, "
            f"you need to translate from {source_locale} to {target_locale}, pls note that you target language is {target_locale}, "
            "you give me the result line by line:\n"
            f"{joined_strings}\n"
            "If you are unable to translate a string, "
            "please provide the original text as the translation."
        )

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system",
                 "content": f"You are a great translation assistant. Your input language is {source_locale} and your output language is {target_locale}."},
                {"role": "user", "content": prompt},
            ]
        )

        if response.choices[0].finish_reason == "length":
            return self.split_and_translate(string_list, source_locale, target_locale)
        else:
            translated_chunk_raw = response.choices[0].message.content.strip().split('\n')
            translated_chunk = [re.sub(r'^\d+[.: ]?', '', text) for text in translated_chunk_raw]

            return translated_chunk

    def translate(self, source_locale, target_locale, strings):
        string_list = [string.data for string in strings]
        total_tokens = self.get_tokens_num(' '.join(string_list))
        num_chunks = max(1, (total_tokens // 1800) + 1)
        chunks = self.get_chunked_strings(strings, num_chunks)

        translated_text = []

        for chunk in chunks:
            translated_text += self.translate_chunk(chunk, source_locale, target_locale)

        print(f"Length of input strings: {len(strings)}")
        print(f"Length of translated text: {len(translated_text)}")

        if len(strings) != len(set(strings)):
            print("Input strings contain duplicate values.")

        result = {
            original_string: StringValue.from_plaintext(translated)
            for original_string, translated in zip(strings, translated_text)
        }

        return result

    def can_translate(self, source_locale, target_locale):
        return source_locale.language_code != target_locale.language_code
