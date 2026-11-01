"""Ask the AI for structured content, with one retry and the numbers guard."""

from pydantic import BaseModel

from app.ai.providers import TextModel
from app.analysis.guard import find_unsupported_numbers
from app.analysis.schema import parse_content, text_fields

MALFORMED_NOTE = (
    "\n\nYour previous answer was not a valid JSON object with all the required keys. "
    "Answer again with only the JSON object."
)


class AnalysisUnreadable(Exception):
    pass


def unsupported_numbers(content: BaseModel, allowed: set[float]) -> list[str]:
    return [n for text in text_fields(content) for n in find_unsupported_numbers(text, allowed)]


def _numbers_note(unsupported: list[str]) -> str:
    return (
        "\n\nYour previous answer used numbers that are not in DATA: "
        f"{', '.join(dict.fromkeys(unsupported))}. Answer again using only numbers from DATA."
    )


def generate_structured[T: BaseModel](
    model: TextModel, prompt: str, allowed: set[float], cls: type[T]
) -> tuple[T, bool]:
    """Return (content, flagged). At most two AI calls: the answer plus one retry for any
    reason. A readable answer that still has unsupported numbers is kept, flagged."""
    first = parse_content(model.complete_json(prompt), cls)
    if first is None:
        second = parse_content(model.complete_json(prompt + MALFORMED_NOTE), cls)
        if second is None:
            raise AnalysisUnreadable
        return second, bool(unsupported_numbers(second, allowed))

    unsupported = unsupported_numbers(first, allowed)
    if not unsupported:
        return first, False
    second = parse_content(model.complete_json(prompt + _numbers_note(unsupported)), cls)
    if second is None:
        return first, True
    return second, bool(unsupported_numbers(second, allowed))
