from textual.app import App, ComposeResult
from textual.widgets import Header, Footer

from juju.tui.screens.chat import ChatScreen


class JujuApp(App):
    CSS_PATH = "../styles/app.tcss"

    def on_mount(self) -> None:
        self.push_screen(ChatScreen())


def run():
    app = JujuApp()
    app.run()


if __name__ == "__main__":
    run()
