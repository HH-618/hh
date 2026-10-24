import json
import time
from typing import Callable, Iterator, List, Dict, Any, Optional

from openai import OpenAI

from juju.core.config import load_settings


class ChatEngine:
    def __init__(self, client: OpenAI = None, tools: List[Dict[str, Any]] = None, tool_runner: Callable = None, model: str = None):
        if client is None:
            settings = load_settings()
            client = OpenAI(base_url=settings.llm.api_url, api_key=settings.llm.api_key)
            if model is None:
                model = settings.llm.model_name
        self.client = client
        self.model = model
        self.tools = tools or []
        self.tool_runner = tool_runner
        self.messages: List[Dict[str, Any]] = []

    def add_user(self, content: str):
        self.messages.append({"role": "user", "content": content})

    def stream_chat(self, on_content: Optional[Callable[[str], None]] = None, on_tool_call_start: Optional[Callable] = None, on_tool_call_delta: Optional[Callable] = None, on_tool_call_end: Optional[Callable] = None):
        while True:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                tools=self.tools if self.tools else None,
                stream=True,
            )
            reply = ""
            tool_calls = {}
            for chunk in stream:
                delta = chunk.choices[0].delta
                if delta.content:
                    reply += delta.content
                    if on_content:
                        on_content(delta.content)
                    else:
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
                self.messages.append(
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
                    result = ""
                    if self.tool_runner:
                        result = self.tool_runner(tc["name"], tc["arguments"])
                    else:
                        result = f"错误: 未配置工具执行器"
                    self.messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tc["id"],
                            "content": result,
                        }
                    )
                continue  # loop again to get response after tool results
            self.messages.append({"role": "assistant", "content": reply})
            if on_content is None:
                print()
            break
        return reply
