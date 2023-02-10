from __future__ import annotations

from hashlib import sha512
from time import time
from typing import Dict, Any, Tuple, Union, List

import requests

from .types import FabDeck, FabCard, FabCardResults


class FabDBError(RuntimeError): 
    """
    An error type for unexpected response codes from fabdb
    """
    def __init__(self, content, status_code):
        super().__init__(f"FabDB Error {status_code}: {content}")


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
        if result.headers.get("Content-Type") != "application/json":
            # TODO - better error here
            raise FabDBError(result.headers, result.status_code)

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
