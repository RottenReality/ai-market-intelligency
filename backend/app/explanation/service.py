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


def _generate(model: ExplanationModel, prompt: str) -> str:
    # Only the model call is wrapped: a bug in our own code must not look like an AI outage.
    try:
        return model.generate(prompt).strip()
    except Exception as error:  # providers raise their own error types
        raise ExplanationFailed(str(error)) from error


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
    text = _generate(model, prompt)
    unsupported = find_unsupported_numbers(text, allowed)
    if unsupported:
        text = _generate(model, _retry_prompt(prompt, unsupported))
        unsupported = find_unsupported_numbers(text, allowed)

    explanation = Explanation(
        iso3=scorecard.country.iso3,
        text=text,
        flagged=bool(unsupported),
        created_at=datetime.now(UTC).isoformat(timespec="seconds"),
    )
    cache.put(key, explanation)
    return explanation
