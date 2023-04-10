from typing import List

from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.message import Message, MessageTarget
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Input

from fabdb.client import FabCardDiff, FabDeckDiff
from fabdb.tui.card_search import CardListButton
from fabdb.tui.deck_list import DeckListWidget, DeckSelector, FabDeckBrowser
from fabdb.tui.types import TUICard
from fabdb.tui.widgets import CardWidget

class CardDiffListButton(CardListButton):
    """
    A CardListButton taylored for FabCardDiffs
    """
    def __init__(self, card: TUICard, diff: FabCardDiff, **kwargs):
        super().__init__(card, **kwargs)
        self.diff = diff
        self.renderable = self._make_renderable()

    def _make_renderable(self) -> str:
        """
        Returns a stylized version of this button's text
        """
        ret = []
        lines = self.diff.long.splitlines()
        for l in lines:
            if l.startswith("+"):
                ret.append(f"[green]{l}[/green]")
            elif l.startswith("-"):
                ret.append(f"[red]{l}[/red]")
            else:
                ret.append(l)
        return "\n".join(ret)


class DeckDiffListWidget(DeckListWidget):
    """
    A special DeckListWidget that handles card diffs instead
    """
    def _mount_section(self, title: str, cards: List[FabCardDiff]) -> None:
        self.mount(Static(title, classes="deck-section"))
        for c in cards:
            self.mount(CardDiffListButton(TUICard(c.card), c, classes="card-entry"))


class DeckDiffSelector(DeckSelector):
    """
    Allows entry of two deck slugs for diffing
    """
    class DeckDiffSearch(Message):
        def __init__(self, sender: MessageTarget, a_query: str, b_query: str):
            super().__init__(sender)
            self.a_query = a_query
            self.b_query = b_query

    def compose(self) -> ComposeResult:
        yield Static("Deck Search", id="title")
        yield Static("Deck URL or ID:", classes="label")
        # TODO - placeholder values for easier testing
        yield Input(value="JReVoRdW", placeholder="Deck A", id="deck-id-a")
        yield Static("Deck URL or ID:", classes="label")
        yield Input(value="gZyJJoDw", placeholder="Deck B", id="deck-id-b")

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        self.log(f"Searching for two decks!")
        # don't call the event handler of the parent class
        event.prevent_default()
        await self.post_message(
            self.DeckDiffSearch(
                self,
                self.query_one("#deck-id-a").value,
                self.query_one("#deck-id-b").value,
            )
        )


class FabDeckDiffBrowser(FabDeckBrowser):
    """
    A FabDeckBrowser that searches for and diffs two decks
    """
    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(DeckDiffListWidget(), id="card-list")
        yield Vertical(
            CardWidget(),
            id="right-panel",
        )
        yield DeckDiffSelector(id="search-panel")
        yield Footer()

    def on_deck_diff_selector_deck_diff_search(self, event: DeckDiffSelector.DeckDiffSearch) -> None:
        a = self.client.get_deck(event.a_query)
        b = self.client.get_deck(event.b_query)
        self.deck = FabDeckDiff(a, b)
        self.action_toggle_search()
        self.log(self.deck)
        self.query_one("CardListWidget").card_list = self.deck
        #self.query_one("CardListWidget").query("CardListbutton").first().focus()
