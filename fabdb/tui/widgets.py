from typing import Any

from textual.app import ComposeResult
from textual.containers import Container
from textual.reactive import reactive
from textual.widgets import Static, Input

from fabdb.client import CARD_TYPES


ALL_COLORS = [
    "red",
    "yellow",
    "blue",
    "none",
]


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
            Static("", id="keywords"),
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
        self.remove_class(*ALL_COLORS)
        self.remove_class(*CARD_TYPES)

        # set new color
        self.add_class(self.card.pitch.name)

        # set new type
        self.add_class(self.card.type)

        # set text values
        self.query_one("#name").update(self.card.name)
        self.query_one("#pitch").update(self.card.top_left)
        self.query_one("#cost").update(self.card.top_right)
        self.query_one("#rules").update(self.card.styled_rules)
        self.query_one("#keywords").update(self.card.styled_keywords)
        self.query_one("#flavor").update(get_or_default(self.card, "flavor", ""))
        self.query_one("#power").update(self.card.bottom_left)
        self.query_one("#block").update(self.card.bottom_right)
