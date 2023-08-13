import string
from retrying import retry
from bs4 import BeautifulSoup
import html
import logging

from wagtail_localize.machine_translators.base import BaseMachineTranslator
import openai
import os
from wagtail_localize.strings import StringValue
from dotenv import load_dotenv, set_key
import tiktoken
import re
from typing import Tuple, List

logger = logging.getLogger('django')
def split_at_last_newline(text):
    parts = re.split(r'(?<!\n)\n', text)
    return [part + '\n' if '\n' in part else part for part in parts]


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
        raise NotImplementedError(
            f"""num_tokens_from_messages() is not implemented for model {model}. See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens.""")
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
        strings_list = [string.render_text() for string in strings]
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
        # Join all strings, preface each string with its index number for clear separation
        joined_strings = '<br/>'.join([f"{i}: {string}" for i, string in enumerate(string_list)])
        num = len(string_list)
        # Describe the task for the model, include the task itself, the language of the text and the language it needs to be translated into
        prompt = (
            f"I have several paragraphs from a source text that need to be translated from {source_locale} to {target_locale}. pls note that your target language is {target_locale}.\n "
            f"Here are the paragraphs:\n"
            f"{joined_strings}\n"
            "Please note that wherever there's  '<br/>' in the source text, you should also include it in the translated text.\n "
            f"Also, this translation should be {num} lines from 0 to {num-1} .\n"
        )

        # System message for setting up the role of the model
        system_message = f"You are a highly skilled translat. Your task is to translate texts from Chinese to other languages."
        initial_user_message = "I have several paragraphs from a source text that need to be translated from Simplified Chinese to English. pls note that your target language is English.\n Here are the paragraphs:\n0: 天赋是命运给的诅咒<br/>1: 年老时要偿还本息<br/>2: 又怎么能容许失去？<br/>3: 可谁又能敌得过溶溶岁月？<br/>4: 虚张声势也好<br/>5: 背水一战也好<br/>6: 那些动人的光彩会注定消散<br/>7: 请慢些吹<br/>8: 来埋葬年轻的自己<br/>9: 玩味地留一丝可供缅怀的痕迹<br/>10: 给我们一首诗歌的时间\nPlease note that wherever there's  '<br/>' in the source text, you should also include it in the translated text. pls also note that you need to keep the source text number same as the target text number, for example this is 11 line text, the result should also be 11 lines."
        initial_assistant_message = '''0: Talent is the curse given by fate.<br/>
1: In old age, one must repay the principal and interest.<br/>
2: How could we allow ourselves to lose?<br/>
3: But who can withstand the melting years?<br/>
4: Making an empty show is fine,<br/>
5: Making a last stand with one's back against the wall is also fine,<br/>
6: Those enchanting radiances are destined to dissipate,<br/>
7: Please take your time to blow,<br/>
8: Come, bury the young self,<br/>
9: Playfully leave a trace for reminiscence,<br/>
10: Give us time for a poem.<br/>'''

        # Create a conversation with the model
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": initial_user_message},
                {"role": "assistant", "content": initial_assistant_message},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3
        )

        # Check if the translation was cut-off due to length
        if response.choices[0].finish_reason == "length":
            return self.split_and_translate(string_list, source_locale, target_locale)
        else:
            # Split the response into separate translations
            if "<br/>" in response.choices[0].message.content:
                content = response.choices[0].message.content.strip()
                content = content.replace("\n\n", "<br/>")
                translated_chunk_raw = content.split("<br/>")
            else:
                translated_chunk_raw = re.findall(r'\d+: ([^\n]*)', response.choices[0].message.content.strip())
            translated_chunk_raw = [text.strip() for text in translated_chunk_raw if text.strip()]
            # Remove any digits, periods, colons or spaces at the start of each translation
            translated_chunk = [re.sub(r'^[\n]+', '', text) for text in translated_chunk_raw]
            translated_chunk = [re.sub(r'^\d+[.: ]?', '', text) for text in translated_chunk]

            # Raise an error if the number of translated strings does not match the number of input strings
            if len(translated_chunk) != len(string_list):
                logger.debug(response.choices[0].message.content.strip())
                logger.error(f"translated strings is {len(translated_chunk)}, source strings is{len(string_list)}")
                raise RuntimeError("The number of translated strings does not match the number of input strings.")

            return translated_chunk

    def translate_text(self, string, source_locale, target_locale):
        total_tokens = self.get_tokens_num(string)
        num_chunks = max(1, (total_tokens // 7000) + 1)
        chunks = self.get_chunked_strings([string], num_chunks)

        translated_text = []

        for chunk in chunks:
            translated_text += self.translate_chunk(chunk, source_locale, target_locale)


        return translated_text

    def translate(self, source_locale, target_locale, strings):
        string_list = [string.render_text() for string in strings]
        total_tokens = self.get_tokens_num(' '.join(string_list))
        num_chunks = max(1, (total_tokens // 6000) + 1)
        chunks = self.get_chunked_strings(strings, num_chunks)
        logger.info(f"Number of chunks: {len(chunks)} and number of strings: {len(strings)}")

        translated_text = []

        for chunk in chunks:
            translated_text += self.translate_chunk(chunk, source_locale, target_locale)

        logger.info(f"Length of input strings: {len(strings)}")
        print(f"Length of translated text: {len(translated_text)}")

        if len(strings) != len(translated_text):
            print("values not matching")

        result = {
            original_string: StringValue.from_plaintext(translated)
            for original_string, translated in zip(strings, translated_text)
        }

        return result

    def can_translate(self, source_locale, target_locale):
        return source_locale.language_code != target_locale.language_code
