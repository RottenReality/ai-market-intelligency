from app.deps import get_explanation_model
from app.evidence.store import EvidenceStore
from tests.explanation.test_prompt import FULL
from tests.scoring.evidence_factory import USA, evidence


class ExplodingModel:
    def generate(self, prompt: str) -> str:
        raise AssertionError("the PDF export must never call the LLM")


def seed(settings):
    EvidenceStore(settings.db_path).upsert(
        [*evidence("COL", FULL).values(), *evidence("USA", USA).values()]
    )


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
    auth_client.app.dependency_overrides[get_explanation_model] = lambda: ExplodingModel()
    assert auth_client.get("/api/reports/pdf", params={"iso3": "COL"}).status_code == 200


def test_country_without_data_returns_409(auth_client):
    response = auth_client.get("/api/reports/pdf", params={"iso3": "COL"})
    assert response.status_code == 409


def test_unknown_code_returns_404_and_empty_returns_422(auth_client):
    assert auth_client.get("/api/reports/pdf", params={"iso3": "XYZ"}).status_code == 404
    assert auth_client.get("/api/reports/pdf", params={"iso3": ""}).status_code == 422


def test_pdf_requires_session(client):
    assert client.get("/api/reports/pdf", params={"iso3": "COL"}).status_code == 401
