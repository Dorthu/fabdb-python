from __future__ import annotations

from enum import Enum
from hashlib import sha512
from time import time
from typing import Dict, Any, Tuple, Union, List

import requests


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


class FabDBError(RuntimeError): 
    """
    An error type for unexpected response codes from fabdb
    """
    def __init__(self, content, status_code):
        super().__init__(f"FabDB Error {status_code}: {content}")


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
        self.flavor = info.get("flavor")
        self.comments = info.get("comments")
        self.image_url = info.get("image")
        self.artist = FabCardArtist(info.get("artist", {}))
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

    def __repr__(self) -> str:
        """
        A string represeentation of this card
        """
        pitch_string = f"({self.pitch.name})" if self.pitch != PitchValue.none else ""
        return f"{self.name} {pitch_string}"

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

        self.cards = self.sideboard = []
        self._load_cards(info.get("cards", []), self.cards)
        self._load_cards(info.get("sideboard", []), self.sideboard)

    def _load_cards(self, cards: List[Dict], into: List):
        """
        Loads the incoming array of fab card data into the given list (deck or sideboard)
        """
        new_cards = [FabDeckCard(c) for c in cards]
        into += new_cards

    def __repr__(self) -> str:
        return f"{self.name}"


class FabDBClient:
    """
    A client class for fabdb.net based on the python requests library
    """
    def __init__(self, api_key: str = None, secret_key: str = None, base_url: str = "api.fabdb.net"):
        """
        Creates a new FabDB Client with optional authentication.  If authentication
        is not provided, requests will be sent unauthenticated.

        :param api_key: The Public API Key for signing the request
        :param secret_key: The Secret Key for hasing the requests' timestamp
        :param base_url: The URL of the API root; in practice this shouldn't change
        """
        if (api_key is not None and secret_key is None) or (api_key is None and secret_key is not None):
            raise ValueError("api_key and secret_key must be provided together!")

        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = base_url

    def _get_signature(self) -> Tuple[Dict[str, str], Dict[str, str]]:
        """
        Gets a signature for a request being sent _right now_ (signatures include
        a time component, and thereby cannot be signed in advance).

        :returns: The required attributes to sign a request, given the configured 
                  api key/secret of this client.

                  The first returned elements are additional headers needed for
                  authenticatoin (the "Authorization" header mainly), the
                  second are additional elements to add to the query string
                  (namely the signed "time" component).
        """
        if self.api_key is None:
            # no authorization inculded
            return {}, {}

        # TODO: This doesn't appear to actually do anything; spending in bogus/no credentials
        # works just fine, even for private decks

        cur_time = round(time())
        signing_string = f"{self.secret_key}cur_time"
        signed_time = sha512(signing_string.encode()).hexdigest()

        headers = {"Authorization": f"Bearer {self.api_key}"}
        query = {
            "time": cur_time,
            "hash": signed_time,
        }

        return headers, query

    def _get(self, path: str, query: Dict[str, Any] = None) -> Dict:
        """
        Makes an HTTP GET request to the API; this is mainly intended for internal
        use, and the structure of the response Dict is based on the path given
        """
        if query is None:
            query = {}

        headers, addl_query = self._get_signature()
        query.update(addl_query)

        query_string = "&".join([f"{k}={v}" for k, v in query.items()])
        url = f"https://{self.base_url}/{path}?{query_string}"

        result = requests.get(url, headers=headers)

        if result.status_code != 200:
            raise FabDBError(result.content, result.status_code)

        return result.json()

    def search_cards(
        self,
        keywords: str = None,
        pitch: Union[PitchValue , int] = None,
        cost: int = None, # convert to 1, 2, 3, 4+
        class_: str = None,
        rarity: str = None,
        set_: str = None,
    ) -> FabCardResults:
        """
        Returns a result set of cards based on the included query
        """
        full_query = {
            "keywords": keywords,
            "pitch": pitch,
            "cost": cost,
            "class": class_,
            "rarity": rarity,
            "set": set_,
            # always full pages to minimize number of requests
            "page_size": 100,
        }
        query = {k: v for k, v in full_query.items() if v is not None}

        res = self._get("cards", query)

        return FabCardResults(self, query, res)

    def get_card(self, identifier: str) -> FabCard:
        """
        Returns information about a single card in fabdb
        """
        res = self._get(f"cards/{identifier}")
        return FabCard(res)

    def get_deck(self, slug: str) -> FabDeck:
        """
        Returns a deck from fabdb
        """
        res = self._get(f"decks/{slug}")
        return FabDeck(res)
