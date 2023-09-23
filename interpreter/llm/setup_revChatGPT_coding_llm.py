from .setup_text_llm import setup_text_llm


def setup_revChatGPT_coding_llm(interpreter):
    """
    Takes a text_llm
    returns a Coding LLM (a generator that streams deltas with `message`, 'language', and `code`).
    """
    from os import environ
    # ChatGPTのアクセストークンの入力　詳細は https://github.com/acheong08/ChatGPT#--access-token を参照
    ACCESS_TOKEN =  environ['CHATGPT_ACCESS_TOKEN']
    
    from revChatGPT.V1 import Chatbot

    chatbot = Chatbot(config={
        "access_token": ACCESS_TOKEN,
    })

    def coding_llm(messages):
        inside_code_block = False
        accumulated_block = ""
        language = None

        print("messages_data:" + str(messages))
        user_messages = [item["message"] for item in messages if item["role"] == "user"]
        print("user_messages_data:" + str(user_messages))
        user_message = user_messages[-1]

        before_str_len = 0
        for data in chatbot.ask(user_message):
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
                print("Did we just exit a code block? : "+ res_message)
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
