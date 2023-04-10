from typing import List

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.message import Message, MessageTarget
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Input

from fabdb.client import FabDBClient, FabDeckCard, FabDeckDiff, FabDeck
from fabdb.tui.card_search import CardListButton, CardListWidget
from fabdb.tui.types import TUICard
from fabdb.tui.widgets import CardWidget


class DeckListWidget(CardListWidget):
    """
    Lists cards like a CardListWidget, but includes sections for hero, weapons,
    equipment, cards, and sideboard
    """
    def watch_card_list(self) -> None:
        if self.card_list is None:
            return

        if not isinstance(self.card_list, FabDeck) and not isinstance(self.card_list, FabDeckDiff):
            raise ValueError(
                f"DeckListWidget must only receive FabDecks or FabDeckDiffs, but got {type(self.card_list)}"
            )

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
        self.query("Input").first().focus()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """
        When you press enter in the search box
        """
        self.log(f"Searching for {event.input.value}")
        await self.post_message(self.DeckSearch(self, event.input.value))


class FabDeckBrowser(Screen):
    """
    A screen that allows exploring a FabDeck
    """
    BINDINGS = [
        ("s", "toggle_search", "Search"),
        ("escape", "app.pop_screen", "Back"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(DeckListWidget(), id="card-list")
        yield Vertical(
            DeckStatsWidget(),
            CardWidget(),
            id="right-panel",
        )
        yield DeckSelector(id="search-panel")
        yield Footer()

    def on_mount(self) -> None:
        self.client = FabDBClient()

    def on_card_list_button_focus(self, message: CardListButton.Focus) -> None:
        self.query_one("CardWidget").card = message.card

    def on_deck_selector_deck_search(self, event: DeckSelector.DeckSearch) -> None:
        self.deck = self.client.get_deck(event.query)
        self.action_toggle_search()
        self.query_one("CardListWidget").card_list = self.deck
        self.query_one("DeckStatsWidget").deck = self.deck
        self.query_one("CardListWidget").query("CardListButton").first().focus()

    def action_toggle_search(self) -> None:
        panel = self.query_one("#search-panel")
        if panel.has_class("-hidden"):
            panel.remove_class("-hidden")
            panel.query("Input").first().focus()
        else:
            panel.add_class("-hidden")
