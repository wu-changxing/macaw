import os
from dotenv import set_key
""" @retry(stop_max_attempt_number=3, wait_exponential_multiplier=1000, wait_exponential_max=10000)
    def translate_chunk(self, string_list, source_locale, target_locale):
        # Join all strings, preface each string with its index number for clear separation
        joined_strings = '|||'.join([f"{i}: {string}" for i, string in enumerate(string_list)])
        num = len(string_list)
        # Describe the task for the model, include the task itself, the language of the text and the language it needs to be translated into
        prompt = (
            f"I have several paragraphs from a source text that need to be translated from {source_locale} to {target_locale}. pls note that your target language is {target_locale}.\n "
            f"Here are the paragraphs:\n"
            f"{joined_strings}\n"
            "Please note that wherever there's  '<br/>' '<b>' or '|||' in the source text, you should also include it in the translated text.\n "
            f"Also, this translation should be {num} lines from 0 to {num-1} .\n"
        )

        # System message for setting up the role of the model
        system_message = f"You are a highly skilled translat. Your task is to translate texts from Chinese to other languages."
        initial_user_message = "I have several paragraphs from a source text that need to be translated from Simplified Chinese to English. pls note that your target language is English.\n Here are the paragraphs:\n0: 天赋是命运给的诅咒<br/>1: 年老时要偿还本息<br/>2: 又怎么能容许失去？<br/>3: 可谁又能敌得过溶溶岁月？<br/>4: 虚张声势也好<br/>5: 背水一战也好<br/>6: 那些动人的光彩会注定消散<br/>7: 请慢些吹<br/>8: 来埋葬年轻的自己<br/>9: 玩味地留一丝可供缅怀的痕迹<br/>10: 给我们一首诗歌的时间\nPlease note that wherever there's  '<br/>' in the source text, you should also include it in the translated text. pls also note that you need to keep the source text number same as the target text number, for example this is 11 line text, the result should also be 11 lines."
        initial_assistant_message = '''0: Talent is the curse given by fate.|||
1: In old age, one must repay the principal and interest.|||
2: How could we allow ourselves to lose?|||
3: But who can withstand the melting years?|||
4: Making an empty show is fine,|||
5: Making a last stand with one's back against the wall is also fine,|||
6: Those enchanting radiances are destined to dissipate,|||
7: Please take your time to blow,|||
8: Come, bury the young self,|||
9: Playfully leave a trace for reminiscence,|||
10: Give us time for a poem.|||'''

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
            if "|||" in response.choices[0].message.content:
                content = response.choices[0].message.content.strip()
                translated_chunk_raw = content.split("|||")
            else:
                translated_chunk_raw = re.findall(r'\d+: ([^\n]*)', response.choices[0].message.content.strip())
            translated_chunk_raw = [text.strip() for text in translated_chunk_raw if text.strip()]
            # Remove any digits, periods, colons or spaces at the start of each translation
            translated_chunk = [re.sub(r'^[\n]+', '', text) for text in translated_chunk_raw]
            translated_chunk = [re.sub(r'^\d+[.: ]?', '', text) for text in translated_chunk]

            # Raise an error if the number of translated strings does not match the number of input string            if len(translated_chunk) != len(string_list):
            if len(translated_chunk) != len(string_list):
                logger.debug(response.choices[0].message.content.strip())
                logger.error(f"translated strings is {len(translated_chunk)}, source strings is{len(string_list)}")
                raise RuntimeError("The number of translated strings does not match the number of input strings.")

            return translated_chunk
 """
def update_total_cost(cost):
        current_cost = float(os.getenv("TOTAL_COST", 0))
        new_cost = current_cost + cost
        dotenv_path = '.env'
        set_key(dotenv_path, "TOTAL_COST", str(new_cost))

def get_chunked_strings(strings, num_chunks):
        strings_list = [string.render_text() for string in strings]
        chunk_size = len(strings_list) // num_chunks
        chunks = [strings_list[i:i + chunk_size] for i in range(0, len(strings_list), chunk_size)]
        if len(chunks) > num_chunks:
            chunks[-2].extend(chunks[-1])
            chunks.pop()
        return chunks

