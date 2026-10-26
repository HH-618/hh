from rich.cells import cell_len
from rich.text import Text
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Input, RichLog
from textual.containers import Vertical
from textual import work

from juju.core.agent import AgentService


def _take_prefix_by_cells(text: str, width: int):
    """按显示宽度截取一行，避免中文等宽字符提前换行"""
    used = 0
    for index, char in enumerate(text):
        char_width = cell_len(char)
        if used + char_width > width:
            if index == 0:
                return char, text[1:]
            return text[:index], text[index:]
        used += char_width
    return text, ""


class ChatScreen(Screen):
    BINDINGS = [("ctrl+c", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Vertical(
            RichLog(id="log", markup=False, wrap=True, min_width=1),
            Input(placeholder="Type your message...", id="input"),
        )
        yield Footer()

    def on_mount(self) -> None:
        self._log = self.query_one("#log", RichLog)
        self._input = self.query_one("#input", Input)
        self.agent = AgentService()
        self._reply_buffer = ""
        self._stream_prefix_pending = True
        self._log.write(Text("Juju - TUI Chat (core/tui separated)", style="bold cyan"))

    def _line_width(self) -> int:
        width = self._log.scrollable_content_region.width
        if width <= 0:
            width = self._log.size.width
        if width <= 0:
            width = 80
        width = max(20, width - 1)
        if self._stream_prefix_pending:
            width = max(10, width - cell_len("Juju: "))
        return width

    def _write_stream_line(self, line: str) -> None:
        text = Text()
        if self._stream_prefix_pending:
            text.append("Juju: ", style="bold yellow")
            self._stream_prefix_pending = False
        text.append(line)

        width = self._log.scrollable_content_region.width
        if width <= 0:
            width = self._log.size.width
        if width <= 0:
            width = 80
        self._log.write(text, width=max(1, width), scroll_end=True)

    def _flush_stream_buffer(self, force: bool = False) -> None:
        while True:
            newline = self._reply_buffer.find("\n")
            if newline != -1:
                line = self._reply_buffer[:newline].rstrip("\r")
                self._reply_buffer = self._reply_buffer[newline + 1 :]
                self._write_stream_line(line)
                continue

            if force:
                if self._reply_buffer:
                    self._write_stream_line(self._reply_buffer)
                    self._reply_buffer = ""
                break

            width = self._line_width()
            if cell_len(self._reply_buffer) < width:
                break

            line, self._reply_buffer = _take_prefix_by_cells(self._reply_buffer, width)
            self._write_stream_line(line)

    def _append_stream_content(self, content: str) -> None:
        if not content:
            return
        self._reply_buffer += content
        self._flush_stream_buffer()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        message = event.value
        if not message.strip():
            return
        self._input.value = ""
        user_text = Text()
        user_text.append("You: ", style="bold green")
        user_text.append(message)
        self._log.write(user_text, scroll_end=True)

        self._reply_buffer = ""
        self._stream_prefix_pending = True
        self._send_message(message)

    @work(thread=True)
    def _send_message(self, message: str) -> None:
        def on_content(c: str):
            self.app.call_from_thread(self._append_stream_content, c)

        try:
            self.agent.send_message(message, on_content=on_content)
            self.app.call_from_thread(self._flush_stream_buffer, True)
        except Exception as e:
            self.app.call_from_thread(self._flush_stream_buffer, True)
            error_text = Text()
            error_text.append("Error: ", style="bold red")
            error_text.append(str(e))
            self.app.call_from_thread(self._log.write, error_text, scroll_end=True)
