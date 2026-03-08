from rich.text import Text

def mnemonic(label: str, key: str) -> Text:
    """Helper to return a Rich Text object where the first occurrence 
    (case-insensitive) of 'key' is bold and underlined."""
    t = Text(label)
    try:
        idx = label.lower().index(key.lower())
        t.stylize("bold underline", idx, idx + len(key))
    except ValueError:
        pass  # if not found, just return plain text
    return t
