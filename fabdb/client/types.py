from __future__ import annotations

from enum import Enum
from typing import Dict, Any, Tuple, Union, List


#: CARD_TYPES includes all supertypes for cards
CARD_TYPES = [
    "action",
    "reaction",
    "equipment",
    "hero",
    "instant",
    "item",
    "weapon",
    "resource",
]


class PitchValue(Enum):
    """
    Enumerates all possible pitch values
    """
    none = 0
    red = 1
    yellow = 2
    blue = 3

    def __repr__(self) -> str:
        return self.name

    def __gt__(self, other: int) -> bool:
        return self.value > other

    def __ge__(self, other: int) -> bool:
        return self.value >= other

    def __lt__(self, other: int) -> bool:
        return self.value < other

    def __le__(self, other: int) -> bool:
        return self.value <= other

    def __eq__(self, other: int) -> bool:
        return self.value == other

    @staticmethod
    def from_int(v: int):
        """
        Returns a PitchValue from the given int
        """
        if v is None:
            return PitchValue.none

        if not -1 < v < 4:
            raise ValueError(f"No pitch value {v}")

        if v == 0:
            return PitchValue.none
        if v == 1:
            return PitchValue.red
        if v == 2:
            return PitchValue.yellow
        if v == 3:
            return PitchValue.blue


class FabCardRuling:
    """
    A single ruling for a card
    """
    def __init__(self, info: Dict):
        self.description = info.get("description")
        self.source = info.get("source")
        self.created = info.get("createdAt")
        self.updated = info.get("updatedAt")

        pivot = info.get("pivot", {})
        self.card_id = pivot.get("card_id")
        self.ruling_id = pivot.get("ruling_id")

    def __repr__(self) -> str:
        return f"[{self.ruling_id}] {self.description} ({self.source})"


class FabCardArtist:
    """
    An artist for a Flesh and Blood card
    """
    def __init__(self, info: Dict):
        self.name = info.get("name")
        self.blurb = info.get("blurb")
        self.image_url = info.get("image")
        self.slug = info.get("slug")

    def __repr__(self) -> str:
        return f"{self.name}"


class FabCard:
    """
    A single Flesh and Blood card
    """
    def __init__(self, info: Dict):
        self.identifier = info.get("identifier")
        self.name = info.get("name")
        self.legality = info.get("legality")
        self.rarity = info.get("rarity")
        self.keywords = info.get("keywords")
        self.text = info.get("text")
        self.flavor = info.get("flavour")
        self.falvour = self.flavor # in case you're so inclined
        self.comments = info.get("comments")
        self.image_url = info.get("image")
        artist = info.get("artist")
        if not artist:
            artist = {}
        self.artist = FabCardArtist(artist)
        self.rulings = [FabCardRuling(c) for c in info.get("rulings", [])]

        # TODO - I've never seen these returned
        self._next = info.get("next")
        self._prev = info.get("prev")

        # parse stats
        stats = info.get("stats", {})
        if not isinstance(stats, dict):
            # These come back as ``"stats": []`` in some responses, which breaks
            # the blew parsing
            stats = {}

        self.cost = stats.get("cost")
        self.attack = stats.get("attack")
        self.defense = stats.get("defense")
        self.pitch = PitchValue.from_int(stats.get("resource"))
        self.life = stats.get("life")
        self.intellect = stats.get("intellect")

        # computed keyword-based attributes
        self.type, self.talents, self.subtypes = self._parse_keywords()

    def __repr__(self) -> str:
        """
        A string represeentation of this card
        """
        pitch_string = f"({self.pitch.name})" if self.pitch != PitchValue.none else ""
        return f"{self.name} {pitch_string}"

    def _parse_keywords(self) -> Tuple[str, List[str], List[str]]:
        """
        Parses type, talents, and subtypes for this card.  They are returned in
        that order.

        For example, given this array of keywords, this will be the output::

           ["generic", "action", "attack"]                  ("action", ["generic"], ["attack"])
           ["draconic", "ninja", "action", "attack"]        ("action", ["draconic", "ninja"], ["attack"])
           ["mechanologist", "hero"]                        ("hero", ["mechanologist"], [])
        """
        if self.keywords is None:
            return None, None, None

        for supertype in CARD_TYPES:
            if supertype in self.keywords:
                break

        # assume we found one
        pivot = self.keywords.index(supertype)
        pivot_skip = 1
        if supertype == "reaction":
            # this is either an "attack reaction" or a "defense reaction" - determine which
            supertype = f"{self.keywords[pivot-1]} {supertype}"
            pivot -= 1
            pivot_skip += 1
        talents = self.keywords[:pivot]
        subtypes = self.keywords[pivot+pivot_skip:]
        return supertype, talents, subtypes

    @property
    def image(self):
        """
        Gets and returns the image for this card
        """


class FabDeckCard(FabCard):
    """
    A subclass of FabCard that tracks the total number of the card in a deck
    """
    def __init__(self, info: Dict):
        super().__init__(info)
        self.total = info.get("total")

    def __repr__(self) -> str:
        srepr = super().__repr__()
        return f"{self.total} x {srepr}"


class FabCardResults:
    """
    A result set from querying fabdb for cards.  This class handles paginating
    between the results seamlessly.
    """
    def __init__(self, client: FabDBClient, query: Dict, info: Dict):
        self.client = client
        self.query = query

        meta = info.get("meta")
        self._page_size = meta.get("per_page")
        self._total_pages = meta.get("last_page")
        self._total_results = meta.get("total")

        # initialize empty pages
        self._pages = [None for i in range(self._total_pages)]

        cur_page = meta.get("current_page") - 1
        self._load_page(cur_page, info.get("data", []))

    def _load_page(self, number: int, data: List[Dict]):
        """
        Loads all FabCards on a given page
        """
        page = [
            FabCard(c) for c in data
        ]

        self._pages[number] = page

    def _get_page(self, number: int):
        """
        Fetches the requested page using our configured client
        """
        page_query = {k: v for k, v in self.query.items()}
        page_query["page"] = number+1 # these are one-indexed in the API
        page = self.client._get("cards", page_query)
        self._load_page(number, page.get("data"))

    def __getitem__(self, index: int) -> FabCard:
        """
        Retrieves a single item from the paginated list, loading new pages as needed
        """
        if index >= self._total_results:
            raise IndexError("list index out of range")

        # we need to know which page of results this index is on, and what result
        # on that page it is
        item_page = index // self._page_size
        item_index = index % self._page_size

        if self._pages[item_page] == None:
            self._get_page(item_page)

        page = self._pages[item_page]
        return page[item_index]

    def __len__(self) -> int:
        """
        Returns the total number of items in this result set
        """
        return self._total_results

    def __next__(self) -> FabCard:
        """
        Handles iterating over results
        """
        cur = 0

        while cur < self._total_results:
            yield self[cur]
            cur += 1

        raise StopIteration()

class FabDeck:
    """
    A deck of cards as returned by fabdb
    """
    def __init__(self, info: Dict):
        self.slug = info.get("slug")
        self.name = info.get("name")
        self.format = info.get("format")
        self.notes = info.get("notes")
        self.visibility = info.get("visibility")
        self.card_back = info.get("cardBack")
        self.created = info.get("createdAt")
        self.total_votes = info.get("totalVotes")
        self.my_vote = info.get("myVote")

        self.cards = []
        self.sideboard = []
        self.hero = None
        self.weapons = []
        self.equipment = []
        self._load_cards(info.get("cards", []), self.cards)
        self._load_cards(info.get("sideboard", []), self.sideboard)

        self._sort()

    def _load_cards(self, cards: List[Dict], into: List):
        """
        Loads the incoming array of fab card data into the given list (deck or sideboard)
        """
        for c in cards:
            new_card = FabDeckCard(c)

            if "hero" in new_card.keywords:
                self.hero = new_card
            elif "weapon" in new_card.keywords:
                self.weapons.append(new_card)
            elif "equipment" in new_card.keywords:
                self.equipment.append(new_card)
            else:
                into.append(new_card)

    def __repr__(self) -> str:
        return f"{self.name}"

    def _sort(self) -> None:
        """
        Sorts all card sections by pitch value, then name
        """
        sorter = lambda o: (o.pitch.value, o.name)

        self.cards = sorted(self.cards, key=sorter)
        self.sideboard = sorted(self.sideboard, key=sorter)
        self.weapons = sorted(self.weapons, key=sorter)
        self.equipment = sorted(self.equipment, key=sorter)


