import os

from wagtail_localize.machine_translators.base import BaseMachineTranslator
from wagtail_localize.strings import StringValue

from .gpt_request_handler import handle_translation_requests


def get_chunked_strings(strings, character_budget=6000):
    """Keep segments intact; an oversized segment occupies its own chunk."""
    if character_budget < 1:
        raise ValueError("The character budget must be positive.")
    chunks = []
    chunk = []
    size = 0
    for string in strings:
        text = string.data
        if chunk and size + len(text) > character_budget:
            chunks.append(chunk)
            chunk = []
            size = 0
        chunk.append(text)
        size += len(text)
    if chunk:
        chunks.append(chunk)
    return chunks


class GeminiTranslator(BaseMachineTranslator):
    display_name = "Gemini"

    def translate(self, source_locale, target_locale, strings):
        if not strings:
            return {}
        chunks = get_chunked_strings(strings)
        translated = handle_translation_requests(chunks, source_locale, target_locale)
        if len(strings) != len(translated):
            raise RuntimeError("The number of translated strings does not match the input.")
        return {
            original: StringValue.from_translated_html(text)
            for original, text in zip(strings, translated)
        }

    def can_translate(self, source_locale, target_locale):
        return bool(os.environ.get("GEMINI_API_KEY")) and (
            source_locale.language_code != target_locale.language_code
        )
