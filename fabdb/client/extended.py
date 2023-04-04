from typing import List

from fabdb.client import FabCard, FabDeck, FabDeckCard


class FabCardDiff(FabCard):
    """
    FabCardDiff is a FabCard that includes additional fields representing its
    appearance in two FabDecks
    """
    def __init__(self, a: FabDeckCard, b: FabDeckCard):
        """
        Creates a card diff.  a and b are expected to be representations of the
        same card (by name and pitch value)
        """
        if a is not None and b is not None and not FabCard.__eq__(a, b):
            raise ValueError(
                f"FabCardDiff must receive two of the same card; got {a} and {b}"
            )

        if a is None and b is None:
            raise ValueError("Cannot diff two absent cards!")

        self.card = a if a is not None else b
        super().__init__(self.card._raw_info)
        self.a = a
        self.b = b

        # compute the actual difference between a and b
        self.delta = 0
        if a is None:
            self.delta = b.total
        elif b is None:
            self.delta = -a.total
        else:
            self.delta = b.total - a.total

        self.diff = ""
        if self.delta > 0:
            self.diff = "+" * self.delta
        elif self.delta < 0:
            self.diff = "-" * (-1 * self.delta)

    def __repr__(self) -> str:
        return f"{self.diff} {FabCard.__repr__(self.card)}"

    @property
    def long(self) -> str:
        if self.delta == 0:
            return str(self.card)
        if self.a is None:
            return f"+ {self.card}"
        elif self.b is None:
            return f"- {self.card}"
        else:
            return f"- {self.a}\n+ {self.b}"


class FabDeckDiff:
    """
    Computes a diff of two decks and allows easy access of it
    """
    def __init__(self, a: FabDeck, b: FabDeck):
        self.a = a
        self.b = b

        # these cards intentionally mirror those in a FabDeck to allow
        # a similar interface
        self.cards = []
        self.sideboard = []
        self.hero = None
        self.weapons = []
        self.equipment = []

        self._compute_diff()

    def _compute_diff(self) -> None:
        """
        Actually handles diffing the two decks
        """
        self.hero = FabCardDiff(self.a.hero, self.b.hero)
        self.weapons = self._diff_cards(self.a.weapons, self.b.weapons)
        self.equipment = self._diff_cards(self.a.equipment, self.b.equipment)
        self.cards = self._diff_cards(self.a.cards, self.b.cards)
        self.sideboard = self._diff_cards(self.a.sideboard, self.b.sideboard)

    def _diff_cards(self, a: List[FabDeckCard], b: List[FabDeckCard]) -> List[FabCardDiff]:
        """
        Returns a list of FabCardDiffs comparing the two lists of FabDeckCards passed in.  This assumes
        that the incoming lists are sorted in the manner of FabDeck._sort
        """
        result = []
        a_pos = b_pos = 0
        while a_pos < len(a) and b_pos < len(b):
            ca = a[a_pos]
            cb = b[b_pos]
            
            # we don't want to consider totals here, just if they're the same card
            if FabCard.__eq__(ca, cb): 
                result.append(FabCardDiff(ca, cb))
                a_pos += 1
                b_pos += 1
            # I think this comparison is wrong - implement __lt__ and __gt__ in FabCard to do it right
            elif ca.pitch < cb.pitch or ca.name < cb.name:
                # card is only in a
                result.append(FabCardDiff(ca, None))
                a_pos += 1
            else:
                # card is only in b
                result.append(FabCardDiff(None, cb))
                b_pos += 1

        if a_pos < len(a):
            # add remaining cards from a
            result += [FabCardDiff(c, None) for c in a[a_pos:]]
        elif b_pos < len(b):
            # add remaining cards from b
            result += [FabCardDiff(c, None) for c in b[b_pos:]]

        return result
