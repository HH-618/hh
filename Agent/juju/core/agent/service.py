from typing import Optional, Callable, Any

from juju.core.llm import ChatEngine
from juju.core.tools import get_tools_schema, run_tool


class AgentService:
    def __init__(self, model: str = None):
        self.engine = ChatEngine(
            tools=get_tools_schema(),
            tool_runner=run_tool,
            model=model,
        )

    def send_message(self, message: str, on_content: Optional[Callable[[str], None]] = None):
        self.engine.add_user(message)
        return self.engine.stream_chat(on_content=on_content)

    @property
    def messages(self):
        return self.engine.messages
