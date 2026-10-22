import configparser
import time

from openai import OpenAI

config = configparser.ConfigParser()
config.read("config.ini")

client = OpenAI(
    base_url=config["llm"]["api_url"],
    api_key=config["llm"]["api_key"],
)

messages = []

while True:
    user_msg = input("You: ")
    messages.append({"role": "user", "content": user_msg})
    try:
        stream = client.chat.completions.create(
            model=config["llm"]["model_name"],
            messages=messages,
            stream=True,
        )
        reply = ""
        for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                reply += content
                for char in content:
                    print(char, end="", flush=True)
                    time.sleep(0.02)
        messages.append({"role": "assistant", "content": reply})
        print()
    except Exception as e:
        print(f"Error: {e}")
