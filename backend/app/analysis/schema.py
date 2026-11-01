"""Structured content the AI must return, and tolerant parsing of its JSON answer."""

import json
import re
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ValidationError


def _non_blank(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("must not be empty")
    return value


Text = Annotated[str, AfterValidator(_non_blank)]


def _trimmed(limit: int):
    def check(items: list[str]) -> list[str]:
        if not items:
            raise ValueError("must have at least one item")
        return items[:limit]

    return AfterValidator(check)


class DimensionTexts(BaseModel):
    Cultural: Text
    Administrative: Text
    Geographic: Text
    Economic: Text


class CountryAnalysisContent(BaseModel):
    executive_summary: Text
    dimensions: DimensionTexts
    barriers: Annotated[list[Text], _trimmed(3)]
    opportunities: Annotated[list[Text], _trimmed(3)]
    recommendation: Text


class RankingText(BaseModel):
    iso3: Text
    explanation: Text


class ComparisonInsightContent(BaseModel):
    summary: Text
    ranking: list[RankingText]
    key_differences: Annotated[list[Text], _trimmed(4)]


# Free models often wrap JSON in a markdown code fence even when asked not to.
_FENCE = re.compile(r"^\s*```(?:json)?\s*(.*?)\s*```\s*$", re.DOTALL | re.IGNORECASE)


def parse_content[T: BaseModel](raw: str, cls: type[T]) -> T | None:
    match = _FENCE.match(raw)
    text = match.group(1) if match else raw
    try:
        return cls.model_validate(json.loads(text))
    except (ValueError, ValidationError):
        return None


def text_fields(content: BaseModel) -> list[str]:
    """Every string inside the content, for the numbers guard."""
    found: list[str] = []

    def walk(value) -> None:
        if isinstance(value, str):
            found.append(value)
        elif isinstance(value, dict):
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(content.model_dump())
    return found
