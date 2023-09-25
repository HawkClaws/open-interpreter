from .setup_text_llm import setup_text_llm
import json
import tokentrim as tt
from os import environ
from ..utils.convert_to_openai_messages import convert_to_openai_messages
# ChatGPTのアクセストークンの入力　詳細は https://github.com/acheong08/ChatGPT#--access-token を参照
ACCESS_TOKEN =  environ.get('CHATGPT_ACCESS_TOKEN')
from revChatGPT.V1 import Chatbot

CHAT_BOT = None
if ACCESS_TOKEN != None:
    CHAT_BOT = Chatbot(config={
        "access_token": ACCESS_TOKEN,
    })

def setup_revChatGPT_coding_llm(interpreter):
    """
    Takes a text_llm
    returns a Coding LLM (a generator that streams deltas with `message`, 'language', and `code`).
    """

    def coding_llm(messages):
        if CHAT_BOT == None:
            raise Exception("revChatGPT initialization failed. Do you have the token set in the environment variable CHATGPT_ACCESS_TOKEN?")
        inside_code_block = False
        accumulated_block = ""
        language = None

        # Convert messages
        messages = convert_to_openai_messages(messages)

        # Seperate out the system_message from messages
        # (We expect the first message to always be a system_message)
        system_message = messages[0]["content"]

        # 謎の文字列を削除
        system_message = system_message.replace('Testing\nOne Two three\n\n\n', '')
        messages = messages[1:]

        # Trim messages, preserving the system_message
        messages = tt.trim(messages=messages, system_message=system_message,max_tokens=4096)

        # print("messages_data:")
        # print(json.dumps(messages, ensure_ascii=False))
        prompt = " ".join([message["content"] for message in messages])
        # print("user_messages_data:" + str(prompt))

        before_str_len = 0
        for data in CHAT_BOT.ask(prompt):
            # chunk['choices'][0]['delta'].get('content', "")
            content = ""
            res_message = data["message"]
            # print("res_message:" + res_message)
            content = res_message[before_str_len:]
            before_str_len = len(res_message)
            accumulated_block += content
            # print("accumulated_block:" + accumulated_block)

            # Did we just enter a code block?
            if "```" in accumulated_block and not inside_code_block:
                inside_code_block = True
                accumulated_block = accumulated_block.split("```")[1]

            # Did we just exit a code block?
            if inside_code_block and "```" in accumulated_block:
                # print("Did we just exit a code block? : "+ res_message)
                return

            if inside_code_block and "`" in accumulated_block:
                continue

            # If we're in a code block,
            if inside_code_block:

                # If we don't have a `language`, find it
                if language is None and "\n" in accumulated_block:
                    language = accumulated_block.split("\n")[0]

                    # Default to python if not specified
                    if language == "":
                        language = "python"

                    output = {"language": language}

                    # If we recieved more than just the language in this chunk, send that
                    if content.split("\n")[1]:
                        output["code"] = content.split("\n")[1]
                    # print(str(output))
                    yield output

                # If we do have a `language`, send the output as code
                elif language:
                    yield {"code": content}

            # If we're not in a code block, send the output as a message
            if not inside_code_block:
                yield {"message": content}

    return coding_llm
