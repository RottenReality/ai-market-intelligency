"""Ask the AI for structured content, with one retry and the numbers and wording guards."""

from typing import NamedTuple

from pydantic import BaseModel

from app.ai.providers import AIProviderError, TextModel
from app.analysis.guard import find_overstatements, find_unsupported_numbers
from app.analysis.schema import parse_content, text_fields

MALFORMED_NOTE = (
    "\n\nYour previous answer was not a valid JSON object with all the required keys. "
    "Answer again with only the JSON object."
)


class AnalysisUnreadable(Exception):
    pass


def unsupported_numbers(content: BaseModel, allowed: set[float]) -> list[str]:
    return [n for text in text_fields(content) for n in find_unsupported_numbers(text, allowed)]


def overstatements(content: BaseModel) -> list[str]:
    return [s for text in text_fields(content) for s in find_overstatements(text)]


class Generated[T: BaseModel](NamedTuple):
    content: T
    flagged: bool  # numbers not in DATA remain
    overstated: bool  # a share of users is still described as a preference


def _fix_note(unsupported: list[str], overstated: list[str]) -> str:
    note = "\n\nYour previous answer had problems. Answer again fixing them."
    if unsupported:
        numbers = ", ".join(dict.fromkeys(unsupported))
        note += f"\n- It used numbers that are not in DATA: {numbers}. Use only numbers from DATA."
    if overstated:
        quoted = " | ".join(dict.fromkeys(overstated))
        note += (
            f"\n- It described a share of users as a preference: {quoted}. A share of people "
            'who use WhatsApp is not a preference: write "use", not "prefer".'
        )
    return note


def _checked[T: BaseModel](content: T, allowed: set[float]) -> Generated[T]:
    return Generated(
        content, bool(unsupported_numbers(content, allowed)), bool(overstatements(content))
    )


def generate_structured[T: BaseModel](
    model: TextModel, prompt: str, allowed: set[float], cls: type[T]
) -> Generated[T]:
    """At most two AI calls: the answer plus one retry for any reason. A readable answer that
    still breaks the numbers or wording rules is kept and marked for review."""
    first = parse_content(model.complete_json(prompt), cls)
    if first is None:
        second = parse_content(model.complete_json(prompt + MALFORMED_NOTE), cls)
        if second is None:
            raise AnalysisUnreadable
        return _checked(second, allowed)

    unsupported, overstated = unsupported_numbers(first, allowed), overstatements(first)
    if not unsupported and not overstated:
        return Generated(first, False, False)
    try:
        retry = model.complete_json(prompt + _fix_note(unsupported, overstated))
    except AIProviderError:
        retry = ""  # e.g. the free per-minute limit: keep the readable first answer, marked
    second = parse_content(retry, cls)
    if second is None:
        return Generated(first, bool(unsupported), bool(overstated))
    return _checked(second, allowed)
