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
from .token_calculation import get_tokens_num,num_tokens_from_messages
from .utils import update_total_cost, get_chunked_strings
from .gpt_request_handler import handle_translation_requests 

logger = logging.getLogger('django')


class ChatGPTTranslator(BaseMachineTranslator):
    display_name = "ChatGpt"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        load_dotenv()
        openai.api_key = os.getenv("OPENAI_API_KEY")

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



    def translate_text(self, string, source_locale, target_locale):
        total_tokens = get_tokens_num(string)
        num_chunks = max(1, (total_tokens // 7000) + 1)
        chunks = get_chunked_strings([string], num_chunks)

        translated_text = []

        for chunk in chunks:
            translated_text += self.translate_chunk(chunk, source_locale, target_locale)


        return translated_text

    def translate(self, source_locale, target_locale, strings):
        string_list = [string.render_text() for string in strings]
        total_tokens = get_tokens_num(' '.join(string_list))
        num_chunks = max(1, (total_tokens // 1000) + 1)
        chunks = get_chunked_strings(strings, num_chunks)
        logger.info(f"Number of chunks: {len(chunks)} and number of strings: {len(strings)}")
        translated_text = []

        # for chunk in chunks:
        #     translated_text += self.translate_chunk(chunk, source_locale, target_locale)
        translated_text, errors = handle_translation_requests(chunks, source_locale, target_locale, max_workers=len(chunks))
        if errors:
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
