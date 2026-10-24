from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Input, RichLog
from textual.containers import Vertical
from textual import work

from juju.core.agent import AgentService


class ChatScreen(Screen):
    BINDINGS = [("ctrl+c", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Vertical(
            RichLog(id="log", markup=True, wrap=False),
            Input(placeholder="Type your message...", id="input"),
        )
        yield Footer()

    def on_mount(self) -> None:
        self._log = self.query_one("#log", RichLog)
        self._input = self.query_one("#input", Input)
        self.agent = AgentService()
        self._log.write("[bold cyan]Juju[/bold cyan] - TUI Chat (core/tui separated)")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        message = event.value
        if not message.strip():
            return
        self._input.value = ""
        self._log.write(f"[bold green]You:[/bold green] {message}")
        self._log.write("[bold yellow]Juju:[/bold yellow] ", scroll_end=True)
        self._send_message(message)

    @work(thread=True)
    def _send_message(self, message: str) -> None:
        def on_content(c: str):
            self.app.call_from_thread(self._log.write, c, scroll_end=True)

        try:
            self.agent.send_message(message, on_content=on_content)
            self.app.call_from_thread(self._log.write, "\n", scroll_end=True)
        except Exception as e:
            self.app.call_from_thread(self._log.write, f"\n[bold red]Error:[/bold red] {e}\n", scroll_end=True)
