from __future__ import annotations

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static
from textual.containers import Container

from fabdb.cli import FabDBCLIConfig


class CardWidget(Static):
    """
    Widget for displaying a single card
    """
    def compose(self) -> ComposeResult:
        yield Static("", id="color-bar")
        yield Container(
            Static("*", id="pitch"),
            Static("Name", id="name"),
            Static("1", id="cost"),
            id="top",
        )

        yield Container(
            Static("This is the rules", id="rules"),
            Static("Flavor", id="flavor"),
            id="rules-box",
        )

        yield Container(
            Static("5", id="power"),
            Static("", id="space"),
            Static("3", id="block"),
            id="bottom",
        )


class FabDBApp(App):
    CSS_PATH="style.css"

    def __init__(self, config: FabDBCLIConfig = None):
        super().__init__()
        self._config = config

    def compose(self) -> ComposeResult:
        yield Header()
        yield CardWidget()
        yield Footer()
