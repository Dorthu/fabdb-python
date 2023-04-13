from enum import Enum
import re
from typing import Any, Callable, List

from fabdb.client import FabCard

class Comparison:
    """
    Abstract base class for all Comparisons
    """
    def __init__(self, matcher: Callable[[Any, Any], bool]):
        self.matcher = matcher

    def matches(self, value: Any, target: Any) -> bool:
        """
        Returns True if the given card matches this comparison, otherwise False
        """
        return self.matcher(value, target)


#: This table defines the supported Comparisons
lookup_table = {
    "lt": Comparison(lambda v, t: v < t),
    "lte": Comparison(lambda v, t: v <= t),
    "gt": Comparison(lambda v, t: v > t),
    "gte": Comparison(lambda v, t: v >= t),
    "eq": Comparison(lambda v, t: v == t),
    "contains": Comparison(lambda v, t: t in v),
    "regex": Comparison(lambda v, t: re.search(t, v, re.IGNORECASE)),
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
        # TODO: Raise ValueError if field isn't a field of FabCard
        self.field = field
        
        if comparison not in lookup_table:
            raise ValueError(
                f"Unknown comparison {comparison}; must be one of "
                f"{', '.join(lookup_table.keys())}",
            )
        self.comparison = lookup_table[comparison]

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
