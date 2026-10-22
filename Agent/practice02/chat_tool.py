import configparser
import subprocess
import time

from openai import OpenAI

config = configparser.ConfigParser()
config.read("config.ini")

client = OpenAI(
    base_url=config["llm"]["api_url"],
    api_key=config["llm"]["api_key"],
)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "getdate",
            "description": "获取当前电脑的日期和时间",
            "parameters": {"type": "object", "properties": {}},
        },
    }
]


def getdate():
    """调用本地 date 命令获取当前日期和时间"""
    try:
        date_str = subprocess.run(
            ["cmd", "/c", "date", "/t"], capture_output=True, text=True
        ).stdout.strip()
        time_str = subprocess.run(
            ["cmd", "/c", "time", "/t"], capture_output=True, text=True
        ).stdout.strip()
        return f"{date_str} {time_str}"
    except Exception as e:
        return f"获取失败: {e}"


messages = []

while True:
    user_msg = input("You: ")
    messages.append({"role": "user", "content": user_msg})
    try:
        while True:
            stream = client.chat.completions.create(
                model=config["llm"]["model_name"],
                messages=messages,
                tools=TOOLS,
                stream=True,
            )
            reply = ""
            tool_calls = {}
            for chunk in stream:
                delta = chunk.choices[0].delta
                if delta.content:
                    reply += delta.content
                    for char in delta.content:
                        print(char, end="", flush=True)
                        time.sleep(0.02)
                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        idx = tc.index
                        if idx not in tool_calls:
                            tool_calls[idx] = {"id": "", "name": "", "arguments": ""}
                        if tc.id:
                            tool_calls[idx]["id"] = tc.id
                        if tc.function:
                            if tc.function.name:
                                tool_calls[idx]["name"] += tc.function.name
                            if tc.function.arguments:
                                tool_calls[idx]["arguments"] += tc.function.arguments
            if tool_calls:
                messages.append(
                    {
                        "role": "assistant",
                        "content": reply or None,
                        "tool_calls": [
                            {
                                "id": tc["id"],
                                "type": "function",
                                "function": {
                                    "name": tc["name"],
                                    "arguments": tc["arguments"],
                                },
                            }
                            for tc in tool_calls.values()
                        ],
                    }
                )
                for tc in tool_calls.values():
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tc["id"],
                            "content": getdate(),
                        }
                    )
                continue
            messages.append({"role": "assistant", "content": reply})
            print()
            break
    except Exception as e:
        print(f"Error: {e}")
