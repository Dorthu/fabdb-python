from __future__ import annotations

from typing import Any
import re

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Button, ListView, ListItem
from textual.containers import Container
from textual.reactive import reactive
from textual.message import Message, MessageTarget

from fabdb.client import (
    FabDBClient,
    FabCard,
    FabDeck,
    FabDeckCard,
    PitchValue,
    CARD_TYPES,
)
from fabdb.cli import FabDBCLIConfig


ALL_COLORS = [
    "red",
    "yellow",
    "blue",
    "none",
]


STYLE_SUBSTITUTIONS = [
    (r"\*\*(.*?)\*\*", r"[b]\1[/b]"), # bolded text - has to come first
    (r"\*(.*?)\*", r"[i]\1[/i]"), # itallic text - must be after bold
    (r"\[(1 )?Resource\]", "[white on red]*[/white on red]"), # resource costs
    (r"\[(Attack|Power)\]", "[on yellow] [/on yellow]"), # attack icon
    (r"\[Life\]", "[on green] [/on green]"), # life icon
    (r"\[Defense\]", "[on grey23] [/on grey23]"), # block icon - TODO doesn't look great
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
        if hasattr(self.card, attr):
            return getattr(self.card, attr)
        return object.__getattribute__(self, attr)

    @property
    def styled_name(self) -> str:
        if self.name is None:
            return ""

        if isinstance(self.card, FabDeckCard):
            return f"{self.total} x {self.name}"
        return self.name

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

        talents = [c.capitalize() for c in self.talents]
        subtypes = [c.capitalize() for c in self.subtypes]
        separator = " - " if subtypes else ""
        return f"{' '.join(talents)} {self.type.capitalize()}{separator}{' '.join(subtypes)}"

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
        if self.type in ("hero", "equipment", "weapon"):
            return ""
        return "0"

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


class CardListButton(Button):
    """
    Pairs a Button with a FabCard
    """
    class Focus(Message):
        def __init__(self, sender: MessageTarget, card: FabCard):
            super().__init__(sender)
            self.card = card

    def __init__(self, card: FabCard, **kwargs):
        super().__init__(card.styled_name, **kwargs)
        self.card = card

    async def on_focus(self) -> None:
        self.log("Running focus!")
        await self.emit(self.Focus(self, self.card))


class CardListWidget(Static): #ListView):
    """
    Lists all cards in a given set and allows selection of them
    """
    BINDINGS = [
        ("up", "focus_previous", "previous"),
        ("down", "focus_next", "next"),
    ]
    card_list = reactive(None)

    def watch_card_list(self) -> None:
        if self.card_list is None:
            return

        for c in self.card_list:
            self.mount(CardListButton(c, classes="card-entry"))

    def on_compose(self) -> ComposeResult:
        pass

    def on_clear(self) -> None:
        entries = self.query(".card-entry")
        for e in entries:
            e.remove()

    def on_card_list_button_focus(self, message: CardListButton.Focus) -> None:
        self.log("Card List caught focus!")

class DeckListWidget(CardListWidget):
    """
    Lists cards like a CardListWidget, but includes sections for hero, weapons,
    equipment, cards, and sideboard
    """
    def watch_card_list(self) -> None:
        if self.card_list is None:
            return

        if not isinstance(self.card_list, FabDeck):
            raise ValueError(f"DeckListWidget must only receive FabDecks, but got {type(self.card_list)}")

        self._mount_section("Hero", [self.card_list.hero])
        self._mount_section("Weapons", self.card_list.weapons)
        self._mount_section("Equipment", self.card_list.equipment)
        self._mount_section("Cards", self.card_list.cards)
        if self.card_list.sideboard:
            self._mount_section("Sidebaord", self.card_list.sideboard)

    def _mount_section(self, title: str, cards: List[FabDeckCard]) -> None:
        # s/mount/append for ListView widget
        self.mount(Static(title, classes="deck-section"))
        for c in cards:
            self.mount(CardListButton(TUICard(c), classes="card-entry"))


class FabDBApp(App):
    CSS_PATH = ["card.css", "card_list.css", "app.css"]

    def __init__(self, config: FabDBCLIConfig = None):
        super().__init__()
        self._config = config

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(DeckListWidget(), id="card-list")
        yield CardWidget()
        yield Footer()

    def on_mount(self) -> None:
        self.client = FabDBClient()
        self.deck = self.client.get_deck("JReVoRdW")
        self.query_one("CardListWidget").card_list = self.deck

    def on_card_list_button_focus(self, message: CardListButton.Focus) -> None:
        self.log("Caught focus!")
        self.query_one("CardWidget").card = message.card
