from __future__ import annotations

from enum import Enum
import re
from typing import Any, Callable, Dict, List

from fabdb.client import FabCard


# we use this to ensure that field passed to CardFilters are valid fields on
# FabCard; we don't care that it has no values populated
CARD_TEMPLATE = FabCard({})

class Comparison:
    """
    Abstract base class for all Comparisons
    """
    def __init__(
        self,
        matcher: Callable[[Any, Any], bool],
        allowed_types: List[Any] = None
    ):
        """
        :param matcher: A callable that returns true if this comparison matches
        :param allowed_types: A list of python types this comparison accepts.  If
                              None (the default), any type is allowed.
        """
        self.matcher = matcher
        self.allowed_types = allowed_types

    def matches(self, value: Any, target: Any) -> bool:
        """
        Returns True if the given card matches this comparison, otherwise False
        """
        if self.allowed_types is not None and type(target) not in self.allowed_types:
            raise ValueError(
                f"Comparison received target {target}, but only supports "
                f"{', '.join([str(c) for c in self.allowed_types])}",
            )

        return self.matcher(value, target)


#: This table defines the supported Comparisons
lookup_table = {
    "lt": Comparison(lambda v, t: v < t, [int, float]),
    "lte": Comparison(lambda v, t: v <= t, [int, float]),
    "gt": Comparison(lambda v, t: v > t, [int, float]),
    "gte": Comparison(lambda v, t: v >= t, [int, float]),
    "eq": Comparison(lambda v, t: v == t),
    "neq": Comparison(lambda v, t: v != t),
    "contains": Comparison(lambda v, t: t in v),
    "regex": Comparison(lambda v, t: re.search(t, v, re.IGNORECASE), [str]),
}


class CardFilter:
    """
    A CardFilter is a single criteria that can be applied to a set of cards to
    get a resulting set of cards that "match" the filter.  These filters are
    applied client-side, and all cards in the set must be fetched from the API
    before they are applied.
    """
    def __init__(self, field: str, comparison: str, target: Any=None):
        """
        :param field: The field that must will be matched on.  Must be a field of
                      FabCard
        :param comparison: The type of comparison we're doing on this field. Must
                           be a comparison type we recognize (defined above).
        :param target: The value we're comparing to.  Must be of a type acceptable
                       to the comparison given.
        """
        if not hasattr(CARD_TEMPLATE, field):
            raise ValueError(
                f"Cannot filter on unknown field {field}; "
                "use a valid field of FabCard",
            )

        self.field = field
        
        if comparison not in lookup_table:
            raise ValueError(
                f"Unknown comparison {comparison}; must be one of "
                f"{', '.join(lookup_table.keys())}",
            )
        self.comparison = lookup_table[comparison]
        self._comparison = comparison

        self.target = target

    def _get_field_value(self, card: FabCard) -> Any:
        """
        Helper function to return the value of the field we're comparing against
        """
        if not hasattr(card, self.field):
            raise ValueError(f"FabCard {card} has no field {self.field}")

        result = getattr(card, self.field)

        if isinstance(result, Enum):
            # PitchValue specifically should be looked at as a number
            return result.value

        return result

    def apply(self, cards: List[FabCard]) -> List[FabCard]:
        """
        Returns a list of FabCards that match this filter from the list of FabCards
        given.
        """
        return [c for c in cards if self.comparison.matches(
            self._get_field_value(c),
            self.target,
        )]

    def to_dict(self) -> Dict[str, Any]:
        """
        Returns this CardFilter as a serialized python dict
        """
        return {
            "field": self.field,
            "comparison": self._comparison,
            "target": self.target,
        }

    @classmethod
    def from_dict(cls, dct: Dict[str, Any]) -> CardFilter:
        """
        Given a python dict, like that from to_dict above, returns a CardFilter
        object with the given values
        """
        if missing := {"field", "comparison", "target"} - set(dct.keys()):
            raise ValueError(f"Keys {', '.join(missing)} are required")

        return CardFilter(
            dct["field"], dct["comparison"], dct["target"],
        )


class Operator(Enum):
    and_ = "and"
    or_ = "or"


class CardMultiFilter(CardFilter):
    """
    Represents a combination of multiple filters; i.e. "All Ice cards that are Blue"
    or "All Attack and Defense Reactions"
    """
    def __init__(self, operator: Operator = Operator.and_, *filters: CardFilter):
        self.operator = operator
        self.filters = filters

    def apply(self, cards: List[FabCard]) -> List[FabCard]:
        """
        Applies all included filters to a card list, returning a list of cards
        matching them
        """
        result_sets = []
        for c in self.filters:
            result_sets.append(set(c.apply(cards)))

        if self.operator == Operator.and_:
            r = result_sets[0]
            for s in result_sets[1:]:
                r = r.intersection(s)
            return list(r)
        raise NotImplemented("Penny woke up!")
