from io import BytesIO

from pypdf import PdfReader

from app.deps import get_ai_models
from app.evidence.store import EvidenceStore
from tests.analysis.fakes import FakeModel, country_content
from tests.analysis.fixtures import FULL
from tests.scoring.evidence_factory import USA, evidence


class ExplodingModel:
    provider = "gemini"
    model = "test"

    def complete_json(self, prompt: str) -> str:
        raise AssertionError("the PDF export must never call the AI")


def seed(settings):
    EvidenceStore(settings.db_path).upsert(
        [*evidence("COL", FULL).values(), *evidence("MEX", FULL).values(),
         *evidence("USA", USA).values()]
    )


def pdf_text(content: bytes) -> str:
    return " ".join(" ".join(p.extract_text() for p in PdfReader(BytesIO(content)).pages).split())


def test_pdf_endpoint_returns_pdf_with_attachment_header(auth_client, settings):
    seed(settings)
    response = auth_client.get("/api/reports/pdf", params={"iso3": "col"})
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    disposition = response.headers["content-disposition"]
    assert disposition.startswith('attachment; filename="market-accessibility-COL-')
    assert disposition.endswith('.pdf"')
    assert response.content.startswith(b"%PDF")


def test_pdf_endpoint_never_calls_the_model(auth_client, settings):
    seed(settings)
    auth_client.app.dependency_overrides[get_ai_models] = lambda: {"gemini": ExplodingModel()}
    assert auth_client.get("/api/reports/pdf", params={"iso3": "COL"}).status_code == 200


def test_country_without_data_returns_409(auth_client):
    response = auth_client.get("/api/reports/pdf", params={"iso3": "COL"})
    assert response.status_code == 409


def test_unknown_code_returns_404_and_empty_returns_422(auth_client):
    assert auth_client.get("/api/reports/pdf", params={"iso3": "XYZ"}).status_code == 404
    assert auth_client.get("/api/reports/pdf", params={"iso3": ""}).status_code == 422


def test_pdf_requires_session(client):
    assert client.get("/api/reports/pdf", params={"iso3": "COL"}).status_code == 401


def test_pdf_includes_saved_analysis_and_comparison_insight(auth_client, settings):
    seed(settings)
    insight_reply = {
        "summary": "SAVED-INSIGHT summary [A1].",
        "ranking": [{"iso3": "COL", "explanation": "Colombia text [A1]."},
                    {"iso3": "MEX", "explanation": "Mexico text [A1]."}],
        "key_differences": ["Language [C1]"],
    }
    auth_client.app.dependency_overrides[get_ai_models] = lambda: {
        "gemini": FakeModel([country_content(executive_summary="SAVED-ANALYSIS [A1]."),
                             insight_reply])
    }
    auth_client.post("/api/countries/COL/analysis", json={"provider": "gemini"})
    auth_client.post("/api/comparison/insight",
                     json={"iso3": ["COL", "MEX"], "provider": "gemini"})
    auth_client.app.dependency_overrides[get_ai_models] = lambda: {"gemini": ExplodingModel()}

    text = pdf_text(auth_client.get("/api/reports/pdf", params={"iso3": "MEX,COL"}).content)
    assert "SAVED-ANALYSIS [A1]." in text
    assert "SAVED-INSIGHT summary [A1]." in text
    single = pdf_text(auth_client.get("/api/reports/pdf", params={"iso3": "COL"}).content)
    assert "SAVED-INSIGHT" not in single
