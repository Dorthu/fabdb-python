from __future__ import annotations

from typing import Any

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static
from textual.containers import Container
from textual.reactive import reactive

from fabdb.client import FabDBClient, FabCard, PitchValue
from fabdb.cli import FabDBCLIConfig


def get_or_default(obj: Any, attr: str, default: Any) -> Any:
    """
    Helper to return a default value if the value isn't set
    """
    val = getattr(obj, attr)
    if val is None:
        return default
    return val


class CardWidget(Static):
    """
    Widget for displaying a single card
    """
    card = reactive(None)

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

    def watch_card(self) -> None:
        """
        Updates the UI when a card changes
        """
        if self.card is None:
            return

        # clear color and class
        self.remove_class("red", "yellow", "blue", "none")
        self.remove_class("hero", "equipment", "weapon", "item", "action", "reaction")

        # set new color
        self.add_class(self.card.pitch.name)

        # set new type
        self.add_class(self.card.type)

        # set text values
        self.query_one("#name").update(get_or_default(self.card, "name", ""))
        self.query_one("#pitch").update("*" * get_or_default(self.card, "pitch", PitchValue.none).value)
        self.query_one("#cost").update(str(get_or_default(self.card, "cost", "")))
        self.query_one("#rules").update(get_or_default(self.card, "text", ""))
        self.query_one("#flavor").update(get_or_default(self.card, "flavor", ""))
        self.query_one("#power").update(str(get_or_default(self.card, "attack", "")))
        self.query_one("#block").update(str(get_or_default(self.card, "defense", "")))



class FabDBApp(App):
    CSS_PATH = ["card.css"]
    BINDINGS = [
        ("a", "advance_type()", "Next Type"),
    ]


    def __init__(self, config: FabDBCLIConfig = None):
        super().__init__()
        self._config = config

    def compose(self) -> ComposeResult:
        yield Header()
        yield CardWidget()
        yield Footer()

    def on_mount(self) -> None:
        self.client = FabDBClient()
        self.cards = [
            self.client.get_card("WTR001"),
            self.client.get_card("UPR086"),
            self.client.get_card("CRU105"),
        ]
        self.current_card = -1
        self.action_advance_type()

    def action_advance_type(self) -> None:
        self.current_card += 1
        if self.current_card >= len(self.cards):
            self.current_card = 0

        self.query_one(CardWidget).card = self.cards[self.current_card]
