from typing import Any

from fabdb.client import FabCard, FabDeckCard
from fabdb.util import richify_rules_text


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

        return richify_rules_text(self.text)

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
