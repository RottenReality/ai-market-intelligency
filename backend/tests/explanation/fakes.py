class FakeModel:
    """Scripted stand-in for an LLM: returns the given replies in order and records prompts."""

    def __init__(self, replies: list[str | Exception]) -> None:
        self.replies = list(replies)
        self.prompts: list[str] = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply


# Numbers that exist in the Colombia test scorecard's DATA block (overall 49, Administrative 23).
CLEAN = "Colombia scores 49% overall. Administrative is the weakest dimension at 23 [A1]."
INVENTED = "Colombia scores 49%, but clients must withhold a 20% tax [A1]."
