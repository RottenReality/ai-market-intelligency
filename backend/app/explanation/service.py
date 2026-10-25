import hashlib
from datetime import UTC, datetime

from app.explanation.cache import Explanation, ExplanationCache
from app.explanation.guard import find_unsupported_numbers, numbers_in
from app.explanation.model import ExplanationModel
from app.explanation.prompt import build_prompt, data_block
from app.profile.company import CompanyProfile, profile_hash
from app.scoring.scorecard import Scorecard


class ExplanationFailed(RuntimeError):
    pass


def cache_key(scorecard: Scorecard, profile: CompanyProfile) -> str:
    payload = scorecard.model_dump_json() + profile_hash(profile)
    return hashlib.sha256(payload.encode()).hexdigest()


def _retry_prompt(prompt: str, unsupported: list[str]) -> str:
    return (
        f"{prompt}\nYour previous answer used numbers that are not in DATA: "
        f"{', '.join(unsupported)}. Rewrite it using only numbers from DATA."
    )


def explain(
    scorecard: Scorecard,
    profile: CompanyProfile,
    *,
    model: ExplanationModel,
    cache: ExplanationCache,
) -> Explanation:
    """Return the cached explanation or generate one. An answer with numbers that are not in
    the data is retried once; if it still has them it is stored but flagged for review."""
    key = cache_key(scorecard, profile)
    if cached := cache.get(scorecard.country.iso3, key):
        return cached

    allowed = numbers_in(data_block(scorecard))
    prompt = build_prompt(scorecard, profile)
    try:
        text = model.generate(prompt).strip()
        unsupported = find_unsupported_numbers(text, allowed)
        if unsupported:
            text = model.generate(_retry_prompt(prompt, unsupported)).strip()
            unsupported = find_unsupported_numbers(text, allowed)
    except Exception as error:  # any provider or network failure
        raise ExplanationFailed(str(error)) from error

    explanation = Explanation(
        iso3=scorecard.country.iso3,
        text=text,
        flagged=bool(unsupported),
        created_at=datetime.now(UTC).isoformat(timespec="seconds"),
    )
    cache.put(key, explanation)
    return explanation
