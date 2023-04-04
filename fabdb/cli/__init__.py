"""
Runs one-off commands on the terminal
"""
from __future__ import annotations

from argparse import ArgumentParser
from configparser import ConfigParser
import os

from rich import print as rprint

from fabdb.client import (
    FabDBClient,
    FabDBError,
    FabDeckDiff,
)
from fabdb.cli.models import FabCliCard, FabCliDeckDiff


class FabDBCLIConfig():
    """
    Encapsulates loading, accessing, and writing a config for the fabdb cli
    """
    def __init__(self, path: str = "~/.config.fabdb-cli"):
        self._config_path = path
        self._config = None
        self._creds = {}

        self._load()

    def _load(self) -> None:
        """
        Loads the config from the configured path if it exists.  If it doesn't exist,
        fails silently
        """
        self._config = ConfigParser()

        path = os.path.expanduser(self._config_path)
        if not os.path.isfile(path):
            # config doesn't exist; that's fine
            return

        try:
            self._config.read(path)
        except:
            # it didn't load; ignore
            return

        self._creds = self._config["creds"] if "creds" in self._config else {}
        
    @property
    def api_creds(self) -> Tuple[str, str]:
        """
        Returns the API credentials found in the config file
        """
        key, secret = self._creds.get("api-key", None), self._creds.get("secret-key", None)
        if key and secret:
            return key, secret
        return None, None


class FabDBCLI():
    def __init__(self, config: FabDBCLIConfig):
        self._config = config
        key, secret = self._config.api_creds
        self._client = FabDBClient(api_key=key, secret_key=secret)

        self._actions = ["deck", "diff", "show", "search"]
        
    def run(self, args: List[str]) -> None:
        """
        Handles a CLI call
        """
        parser = ArgumentParser("fabdb-cli", add_help=False)
        parser.add_argument("action", help=f"One of {', '.join(self._actions)}")
        parsed, remaining = parser.parse_known_args(args)

        if parsed.action in self._actions:
            getattr(self, parsed.action)(remaining)
        else:
            parser.print_help()

    def deck(self, args: List[str]) -> None:
        """
        Shows a deck
        """
        parser = ArgumentParser("fabdb-cli deck")
        parser.add_argument("slug")
        parsed = parser.parse_args(args)

        res = self._client.get_deck(parsed.slug)
        print(res)

    def diff(self, args: List[str]) -> None:
        """
        Diffs two decks by deck codes or URLs
        """
        parser = ArgumentParser("fabdb-cli deck-diff")
        parser.add_argument("deck_a")
        parser.add_argument("deck_b")
        parsed = parser.parse_args(args)

        da = self._client.get_deck(parsed.deck_a)
        db = self._client.get_deck(parsed.deck_b)
        diff = FabCliDeckDiff(FabDeckDiff(da, db))

        rprint(diff.render())

    def show(self, args: List[str]) -> None:
        """
        Shows one card
        """
        parser = ArgumentParser("fabdb-cli show")
        parser.add_argument("slug")
        parser.add_argument("--long", "-l", action="store_true", help="Show long output")
        parsed = parser.parse_args(args)

        res = self._client.get_card(parsed.slug)
        rprint(FabCliCard(res).render(short=not parsed.long))

    def search(self, args: List[str]) -> None:
        """
        Searches for cards and outputs the results
        """
        print("Coming soon..")
