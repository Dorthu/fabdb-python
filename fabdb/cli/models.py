from rich.panel import Panel

from fabdb.client import FabCard, PitchValue, FabCardDiff, FabDeckDiff
from fabdb.util import richify_rules_text


def color_strip(pitch: PitchValue, spacer: int = 0) -> str:
    """
    Returns a rich-rendable string for a color strip
    """
    if pitch == PitchValue.none:
        return ""

    color = pitch.name
    return f"[{color} on {color}]" + (" " * (pitch.value + spacer + 7)) + f"[/{color} on {color}]"

def colorize(text: str, pitch: PitchValue) -> str:
    fg = "white"
    color = pitch.name
    if pitch == PitchValue.none:
        color = "black"
    elif pitch == PitchValue.yellow:
        fg = "black"

    return f"[{fg} on {color}]{text}[/{fg} on {color}]"


class FabCliCard:
    def __init__(self, card: FabCard):
        self.card = card

    def render(self, short=True) -> str:
        """
        Returns a string that we can pretty-print to the terminal
        """
        if short:
            lines = [
                f"{'*' * self.card.pitch.value} {colorize(f' [bold]{self.card.name}[/bold] ', self.card.pitch)} ({self.card.cost})",
                f"{richify_rules_text(self.card.text)}",
                f"[italic]{self.card.flavor or ''}[/italic]",
                f"{self.card.attack or ' '} / {self.card.defense or ' '}",
            ]
            return "\n".join(lines)

        return Panel(f"""{color_strip(self.card.pitch, len(self.card.name))}
[white on red]{"*" * self.card.pitch.value}[/white on red]   {self.card.name}   [white on red]{self.card.cost}[/white on red]

{richify_rules_text(self.card.text)}

[italic]{self.card.flavor}[/italic]

[black on yellow]{self.card.attack or ' '}[/black on yellow]{' ' * (self.card.pitch.value + len(self.card.name) + 7 - len(str(self.card.attack)) - len(str(self.card.defense)))}[white on grey]{self.card.defense or ' '}[/white on grey]
""",
        expand=False,
        width=(self.card.pitch.value + len(self.card.name) + 11),
        border_style="none",
        )

class FabCliDeckDiff:
    def __init__(self, diff: FabDeckDiff):
        self.diff = diff

    def render(self) -> str:
        """
        Outputs a rich-rendered version of the included deck diff
        """
        # first few lines are pretty static
        lines = [
            f"diff --fabdb a:https://fabdb.net/decks/{self.diff.a.slug} b:https://fabdb.net/decks/{self.diff.b.slug}",
            "",
            "[u]Hero:[/u]",
            self._style(self.diff.hero),
            "",
            "[u]Weapons:[/u]",
        ]

        # add a styled line for each weapon
        lines += [self._style(w) for w in self.diff.weapons]

        lines += [
            "",
            "[u]Equipment:[/u]",
        ]
        lines += [self._style(e) for e in self.diff.equipment]

        lines += [
            "",
            "[u]Cards:[/u]",
        ]
        lines += [self._style(c) for c in self.diff.cards]

        if len(self.diff.sideboard):
            lines += [
                "",
                "[u]Sideboard:[/u]",
            ]
            lines += [self._style(c) for c in self.diff.sideboard]

        return "\n".join(lines)

    def _style(self, cdiff: FabCardDiff) -> str:
        """
        Applies rich styling to a single line
        """
        output = []
        for c in cdiff.long.splitlines():
            if c.startswith("-"):
                output += [f"[red]{c}[/red]"]
            elif c.startswith("+"):
                output += [f"[green]{c}[/green]"]
            else:
                output += [f"[white]{c}[/white]"]

        return "\n".join(output)
