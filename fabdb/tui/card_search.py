from textual.app import ComposeResult
from textual.containers import Container
from textual.message import Message, MessageTarget
from textual.reactive import reactive
from textual.widgets import Static, Input

from fabdb.client import FabCard


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
        await self.post_message(self.Focus(self, self.card))


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


class CardSearchPanel(Container):
    """
    A panel that comes up from the bottom of the screen to allow card searching
    """
    class CardSearch(Message):
        def __init__(self,  sender: MessageTarget, keywords: str):
            super().__init__(sender)
            self.keywords = keywords

    def compose(self) -> ComposeResult:
        yield Static("Card Search", id="title")
        yield Static("Keyword:", classes="label")
        yield Input(placeholder="Search Text", id="keywords")

    def on_mount(self) -> None:
        self.query_one("Input").focus()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        self.log(f"Searching for cards with {event.input.value}")
        await self.post_message(self.CardSearch(self, event.input.value))

