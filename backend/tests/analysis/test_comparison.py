import json
from dataclasses import replace

from app.analysis.prompt import comparison_data_block
from app.analysis.schema import RankingText
from app.analysis.service import (
    comparison_subject,
    generate_comparison_insight,
    get_comparison_insight,
    order_ranking,
)
from app.analysis.store import AnalysisStore
from app.deps import get_ai_models
from app.evidence.store import EvidenceStore
from tests.analysis.fakes import FakeModel
from tests.analysis.fixtures import FULL, PROFILE, colombia_scorecard, scorecard_for
from tests.scoring.evidence_factory import USA, evidence

# Mexico: same as Colombia plus a tax treaty and a 2 h gap -> accessibility 64 vs Colombia 49.
MEXICO = {**FULL, "max_hour_diff_home": 2.0, "tax_treaty_with_home": True}
INSIGHT = {
    "summary": "Mexico leads with 64% while Colombia trails by 15 points [A1].",
    "ranking": [{"iso3": "COL", "explanation": "Colombia lacks a tax treaty [A1]."}],
    "key_differences": ["Tax treaty [A1]", "Working hours [G1]"],
}


def mexico_scorecard():
    return scorecard_for("MEX", "Mexico", MEXICO, tz="America/Mexico_City")


def test_subject_is_sorted_codes():
    assert comparison_subject(["MEX", "COL"]) == "COL,MEX"


def test_data_block_contains_ranks_and_gaps():
    data = json.loads(comparison_data_block([colombia_scorecard(), mexico_scorecard()]))
    by_code = {c["iso3"]: c for c in data["countries"]}
    assert (by_code["MEX"]["market_accessibility"], by_code["MEX"]["rank"]) == (64, 1)
    assert by_code["MEX"]["points_behind_leader"] == 0
    assert (by_code["COL"]["rank"], by_code["COL"]["points_behind_leader"]) == (2, 15)
    admin = by_code["COL"]["dimensions"]["Administrative"]
    assert admin == {"score": 23, "rank": 2, "points_behind_leader": 50}


def test_order_ranking_uses_real_scores_and_fills_missing():
    entries = [
        RankingText(iso3="COL", explanation="Colombia lacks a tax treaty."),
        RankingText(iso3="XYZ", explanation="Unknown."),
        RankingText(iso3="COL", explanation="Duplicate."),
    ]
    ranked = order_ranking([colombia_scorecard(), mexico_scorecard()], entries)
    assert [(r.iso3, r.rank) for r in ranked] == [("MEX", 1), ("COL", 2)]
    assert ranked[0].explanation == "No explanation provided"
    assert ranked[1].explanation == "Colombia lacks a tax treaty."
    assert ranked[1].name == "Colombia"


def test_generate_and_get_insight(tmp_path):
    store = AnalysisStore(tmp_path / "app.sqlite")
    cards = [colombia_scorecard(), mexico_scorecard()]
    insight = generate_comparison_insight(cards, PROFILE, FakeModel([INSIGHT]), store)
    assert insight.countries == ["COL", "MEX"]
    assert insight.flagged is False
    assert insight.key_differences == ["Tax treaty [A1]", "Working hours [G1]"]
    assert [r.iso3 for r in insight.ranking] == ["MEX", "COL"]
    assert get_comparison_insight(list(reversed(cards)), PROFILE, store) == insight


def test_outdated_after_profile_change(tmp_path):
    store = AnalysisStore(tmp_path / "app.sqlite")
    cards = [colombia_scorecard(), mexico_scorecard()]
    generate_comparison_insight(cards, PROFILE, FakeModel([INSIGHT]), store)
    edited = replace(PROFILE, supported_languages=["en", "es"])
    assert get_comparison_insight(cards, edited, store).outdated is True


# ---- routes -------------------------------------------------------------------------------


def seed(settings):
    EvidenceStore(settings.db_path).upsert([
        *evidence("COL", FULL).values(), *evidence("MEX", MEXICO).values(),
        *evidence("ESP", FULL).values(), *evidence("USA", USA).values(),
    ])


def post(client, codes):
    return client.post("/api/comparison/insight", json={"iso3": codes, "provider": "gemini"})


def test_countries_without_data_are_dropped_from_subject(auth_client, settings):
    seed(settings)
    auth_client.app.dependency_overrides[get_ai_models] = lambda: {"gemini": FakeModel([INSIGHT])}
    response = post(auth_client, ["COL", "MEX", "CHL"])  # Chile has no data
    assert response.status_code == 200
    assert response.json()["countries"] == ["COL", "MEX"]


def test_fewer_than_two_with_data_returns_422(auth_client, settings):
    seed(settings)
    auth_client.app.dependency_overrides[get_ai_models] = lambda: {"gemini": FakeModel([])}
    response = post(auth_client, ["COL", "CHL"])
    assert response.status_code == 422
    assert response.json() == {"detail": "Select at least two countries with data"}


def test_unknown_code_returns_404(auth_client, settings):
    seed(settings)
    auth_client.app.dependency_overrides[get_ai_models] = lambda: {"gemini": FakeModel([])}
    assert post(auth_client, ["COL", "XYZ"]).status_code == 404


def test_same_set_any_order_finds_insight(auth_client, settings):
    seed(settings)
    auth_client.app.dependency_overrides[get_ai_models] = lambda: {"gemini": FakeModel([INSIGHT])}
    post(auth_client, ["MEX", "COL"])
    found = auth_client.get("/api/comparison/insight", params={"iso3": "COL,MEX"})
    assert found.status_code == 200
    assert found.json()["summary"] == INSIGHT["summary"]


def test_different_set_returns_404(auth_client, settings):
    seed(settings)
    auth_client.app.dependency_overrides[get_ai_models] = lambda: {"gemini": FakeModel([INSIGHT])}
    post(auth_client, ["MEX", "COL"])
    other = auth_client.get("/api/comparison/insight", params={"iso3": "COL,MEX,ESP"})
    assert other.status_code == 404
    assert other.json() == {"detail": "No comparison insight yet"}


def test_insight_requires_session(client):
    assert client.get("/api/comparison/insight", params={"iso3": "COL,MEX"}).status_code == 401
