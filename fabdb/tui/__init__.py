from __future__ import annotations

from typing import Any
import re

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Button, ListView, ListItem, Input
from textual.containers import Container, Vertical, Horizontal
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


class CardListButton(Static):
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

    def on_mount(self) -> None:
        self.can_focus = True

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

class DeckStatsWidget(Static):
    """
    Shows deck stats
    """
    deck = reactive(None)

    def compose(self) -> ComposeResult:
        yield Static("Deck Name", id="deck-name")
        yield Static("Card Counts:", id="card-count-label")
        yield Horizontal(
            Static("Total:", id="card-count"),
            Static("Deck:", id="deck-count"),
            Static("Sideboard:", id="sideboard-count"),
        )
        yield Static("Pitch Curve:")
        yield Horizontal(
            Static(id="none"),
            Static(id="red"),
            Static(id="yellow"),
            Static(id="blue"),
            id="pitch-percentage",
        )

    def watch_deck(self) -> None:
        if self.deck is None:
            return

        self.query_one("#deck-name").update(self.deck.name)

        deck_count = sideboard_count = 0
        for c in self.deck.cards:
            deck_count += c.total
        for c in self.deck.sideboard:
            sideboard_count += c.total

        self.query_one("#card-count").update(f"Total: {deck_count + sideboard_count}")
        self.query_one("#deck-count").update(f"Deck: {deck_count}")
        self.query_one("#sideboard-count").update(f"Sideboard: {sideboard_count}")

        pitch_counts = [0, 0, 0, 0]
        for c in self.deck.cards:
            pitch_counts[c.pitch.value] += c.total

        self.query_one("#pitch-percentage #none").styles.width = f"{pitch_counts[0]}fr"
        self.query_one("#pitch-percentage #red").styles.width = f"{pitch_counts[1]}fr"
        self.query_one("#pitch-percentage #yellow").styles.width = f"{pitch_counts[2]}fr"
        self.query_one("#pitch-percentage #blue").styles.width = f"{pitch_counts[3]}fr"

class DeckSelector(Container):
    """
    A panel that comes up from the bottom of the screen to allow deck switching
    """
    class DeckSearch(Message):
        def __init__(self, sender: MessageTarget, query: str):
            super().__init__(sender)
            self.query = query

    def compose(self) -> ComposeResult:
        yield Static("Deck Search", id="title")
        yield Static("Deck URL or ID:", classes="label")
        yield Input(placeholder="Deck ID", id="deck-id")

    def on_mount(self) -> None:
        self.query_one("Input").focus()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """
        When you press enter in the search box
        """
        self.log("Serach!")
        await self.emit(self.DeckSearch(self, event.input.value))


class FabDBApp(App):
    CSS_PATH = ["card.css", "card_list.css", "app.css"]
    BINDINGS = [
        ("s", "toggle_search", "Search"),
    ]

    def __init__(self, config: FabDBCLIConfig = None):
        super().__init__()
        self._config = config

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(DeckListWidget(), id="card-list")
        yield Vertical(
            DeckStatsWidget(),
            CardWidget(),
            id="right-panel",
        )
        yield DeckSelector()
        yield Footer()

    def on_mount(self) -> None:
        self.client = FabDBClient()

    def on_card_list_button_focus(self, message: CardListButton.Focus) -> None:
        self.log("Caught focus!")
        self.query_one("CardWidget").card = message.card

    def on_deck_selector_deck_search(self, event: DeckSelector.DeckSearch) -> None:
        self.log("deck search!!!")
        self.deck = self.client.get_deck(event.query)
        self.action_toggle_search()
        self.query_one("CardListWidget").card_list = self.deck
        self.query_one("DeckStatsWidget").deck = self.deck
        self.query_one("CardListWidget").query("CardListButton").first().focus()

    def action_toggle_search(self) -> None:
        panel = self.query_one("DeckSelector")
        if panel.has_class("-hidden"):
            panel.remove_class("-hidden")
        else:
            panel.add_class("-hidden")
