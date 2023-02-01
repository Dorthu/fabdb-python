# fabdb-cli

A Command Line Interface and general-purpose library for querying [fabdb](https://fabdb.net)
in python.

## Usage

:warning: Currently under construction :warning:

```python3
from fabdb import FabDBClient

client = FabDBClient()

# one card by ID
nimbilism = client.get_card("nimbilism-yellow")
print(nimbilism.name)


# search cards
ranger_cards = client.search_cards(class_="ranger")
for c in ranger_cards:
  # automatically handles requesting additional pages as needed
  print(c)


# find a deck
deck = client.get_deck("bYDmozyB")
print(deck.name)
print(deck.cards[0])
```

## Coming Soon

* CLI interface
* Textual output formatters
* Interactive/expanded search
* Local card cache
