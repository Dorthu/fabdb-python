from rich.panel import Panel

from fabdb.client import FabCard, PitchValue


def color_strip(pitch: PitchValue, spacer: int = 0) -> str:
    """
    Returns a rich-rendable string for a color strip
    """
    if pitch == PitchValue.none:
        return ""

    color = pitch.name
    return f"[{color} on {color}]" + (" " * (pitch.value + spacer + 7)) + f"[/{color} on {color}]"


class FabCliCard:
    def __init__(self, card: FabCard):
        self.card = card

    def render(self) -> str:
        """
        Returns a string that we can pretty-print to the terminal
        """
        lines = [
            f"[white on red]{'*' * self.card.pitch.value}[/white on red] [bold]{self.card.name}[/bold] [white on red]{self.card.cost}[/white on red]",
            f"{self.card.text}",
            f"[italic]{self.card.flavor}[/italic]",
        ]
        return "\n".join(lines)

        # TODO - I didn't like this output. . . but not enough to delete it
        return Panel(f"""{color_strip(self.card.pitch, len(self.card.name))}
[white on red]{"*" * self.card.pitch.value}[/white on red]   {self.card.name}   [white on red]{self.card.cost}[/white on red]

{self.card.text}

[italic]{self.card.flavor}[/italic]

[black on yellow]{self.card.attack}[/black on yellow]{' ' * (self.card.pitch.value + len(self.card.name) + 7 - len(str(self.card.attack)) - len(str(self.card.defense)))}[white on grey]{self.card.defense}[/white on grey]
""",
        expand=False,
        width=(self.card.pitch.value + len(self.card.name) + 11),
        border_style="none",
        )
