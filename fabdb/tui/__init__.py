from __future__ import annotations

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Button

from fabdb.cli import FabDBCLIConfig
from fabdb.tui.deck_list import FabDeckBrowser
from fabdb.tui.diff import FabDeckDiffBrowser


class FabDBApp(App):
    CSS_PATH = ["card.css", "card_list.css", "app.css"]
    SCREENS = {
        "decks": FabDeckBrowser(),
        "diff": FabDeckDiffBrowser(),
    }
    BINDINGS = [
        ("d", "app.push_screen('decks')", "Deck Search"),
        ("f", "app.push_screen('diff')", "Deck Diff"),
    ]

    def __init__(self, config: FabDBCLIConfig = None):
        super().__init__()
        self._config = config

    def compose(self) -> ComposeResult:
        yield Header()
        yield Button("Deck Browser", id="decks")
        yield Button("Deck Diff Tool", id="diff")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.push_screen(event.button.id)
