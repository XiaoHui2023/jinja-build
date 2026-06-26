def format_title(text: str) -> str:
    return f"《{text.strip()}》"


def slugify(text: str) -> str:
    return text.strip().lower().replace(" ", "-")
