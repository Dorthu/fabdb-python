from rich.panel import Panel

from fabdb.client import FabCard, PitchValue
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
