from __future__ import annotations

from typing import Any
import re

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static
from textual.containers import Container
from textual.reactive import reactive

from fabdb.client import FabDBClient, FabCard, PitchValue
from fabdb.cli import FabDBCLIConfig


ALL_CARD_TYPES = [
    "action",
    "equipment",
    "hero",
    "instant",
    "item",
    "weapon",
]

ALL_COLORS = [
    "red",
    "yellow",
    "blue",
    "none",
]


STYLE_SUBSTITUTIONS = [
    (r"\*\*(.*?)\*\*", r"[b]\1[/b]"), # bolded text - has to come first
    (r"\*(.*?)\*", r"[i]\1[/i]"), # itallic text - must be after bold
    (r"\[Resource\]", "[white on red]*[/white on red]"), # resource costs
    (r"\[Attack\]", "[on yellow] [/on yellow]"), # attack icon
]

ALL_SUBTYPES = [
    "attack",
    "item",
    "head",
    "arms",
    "chest",
    "legs",
    "off-hand",
]


class TUICard():
    """
    Wraps a FabCard and extends it with additional features
    """
    def __init__(self, card: FabCard):
        self.card = card

    def __getattr__(self, attr: str) -> Any:
        """
        Passthrough attributes to the underlying card by default
        """
        print(f"Looking for attr {attr}")
        if hasattr(self.card, attr):
            return getattr(self.card, attr)
        return object.__getattribute__(self, attr)

    @property
    def styled_rules(self) -> str:
        """
        Returns the rules, with styling replaced as expected
        """
        if self.text is None:
            return ""

        styled = self.text
        for pattern, replacement in STYLE_SUBSTITUTIONS:
            styled = re.sub(pattern, replacement, styled)

        return styled

    @property
    def styled_keywords(self) -> str:
        """
        Handles formatting keywords for display
        """
        if self.keywords is None:
            return ""

        keyword_list = self.keywords[:] # copy so we don't modify the original
        for i, val in enumerate(keyword_list):
            if val in ALL_SUBTYPES:
                i -= 1
                break

        if i < len(keyword_list) - 1:
            keyword_list.insert(i+1, "-")

        return " ".join([c.capitalize() for c in keyword_list])

    @property
    def top_left(self) -> str:
        """
        Returns the value to print in the pitch value space at the top left of
        the card
        """
        return "*" * self.pitch.value

    @property
    def top_right(self) -> str:
        """
        Returns the value to print in the cost space at the top right of the card
        """
        if self.cost:
            return str(self.cost)
        return ""

    @property
    def bottom_left(self) -> str:
        """
        Returns the value to print in the bottom-left of the card; either power
        or intellect
        """
        if self.attack is not None:
            return str(self.attack)
        elif self.intellect is not None:
            return str(self.intellect)
        return ""

    @property
    def bottom_right(self) -> str:
        """
        Returns the value to print in the bottom-right of the card; either block
        or health
        """
        if self.defense is not None:
            return str(self.defense)
        elif self.life is not None:
            return str(self.life)
        return ""

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
        self.remove_class(*ALL_CARD_TYPES)

        # set new color
        self.add_class(self.card.pitch.name)

        # set new type
        self.add_class(self.card.type)

        # set text values
        self.query_one("#name").update(get_or_default(self.card, "name", ""))
        self.query_one("#pitch").update(self.card.top_left)
        self.query_one("#cost").update(self.card.top_right)
        self.query_one("#rules").update(self.card.styled_rules)
        self.query_one("#keywords").update(self.card.styled_keywords)
        self.query_one("#flavor").update(get_or_default(self.card, "flavor", ""))
        self.query_one("#power").update(self.card.bottom_left)
        self.query_one("#block").update(self.card.bottom_right)



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
            TUICard(self.client.get_card("WTR001")),
            TUICard(self.client.get_card("UPR086")),
            TUICard(self.client.get_card("CRU105")),
            TUICard(self.client.get_card("throttle-yellow")),
        ]
        self.current_card = -1
        self.action_advance_type()

    def action_advance_type(self) -> None:
        self.current_card += 1
        if self.current_card >= len(self.cards):
            self.current_card = 0

        self.query_one(CardWidget).card = self.cards[self.current_card]
