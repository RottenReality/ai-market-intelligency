import json


class FakeModel:
    """Scripted stand-in for an AI provider: returns replies in order and records prompts."""

    def __init__(self, replies, provider: str = "gemini", model: str = "test-model") -> None:
        self.replies = list(replies)
        self.prompts: list[str] = []
        self.provider = provider
        self.model = model

    def complete_json(self, prompt: str) -> str:
        self.prompts.append(prompt)
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply if isinstance(reply, str) else json.dumps(reply)


def country_content(**overrides) -> dict:
    """A valid analysis that only uses numbers present in the Colombia test DATA (49, 23)."""
    content = {
        "executive_summary": "Colombia scores 49% overall [A1].",
        "dimensions": {
            "Cultural": "A wide cultural gap [C3].",
            "Administrative": "Administrative is the weakest at 23 [A1].",
            "Geographic": "Close in working hours [G1].",
            "Economic": "A large urban market [E2].",
        },
        "barriers": ["No tax treaty [A1]", "Cultural distance [C3]"],
        "opportunities": ["Large cities [E2]", "High internet use [G2]"],
        "recommendation": "Explore a local partner first, then a short pilot.",
    }
    content.update(overrides)
    return content
