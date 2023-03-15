import re

# Card text returned by fabdb uses the following placeholders for symbols and special
# fonts - this is a list of substitutions that can be applied to convert them into
# rich-style strings
STYLE_SUBSTITUTIONS = [
    (r"\*\*(.*?)\*\*", r"[b]\1[/b]"), # bolded text - has to come first
    (r"\*(.*?)\*", r"[i]\1[/i]"), # itallic text - must be after bold
    (r"\[(1 )?Resource\]", "[white on red]*[/white on red]"), # resource costs
    (r"\[2 Resource\]", "[white on red]**[/white on red]"), # some older cards resource costs
    (r"\[3 Resource\]", "[white on red]***[/white on red]"), # some older cards resource costs
    (r"\[(Attack|Power)\]", "[on yellow] [/on yellow]"), # attack icon
    (r"\[Life\]", "[on green] [/on green]"), # life icon
    (r"\[Defense\]", "[on grey23] [/on grey23]"), # block icon - TODO doesn't look great
]

def richify_rules_text(text: str) -> str:
    """
    Returns the input text after having applied the style substitutions above; this
    converts rules text strings from the format returend by fabdb to a format compatible
    with rich
    """
    styled = text
    for pattern, replacement in STYLE_SUBSTITUTIONS:
        styled = re.sub(pattern, replacement, styled)

    return styled
