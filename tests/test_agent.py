import types

from langchain_core.messages import AIMessage

from app.agent import ProductionAgent


class FakeLLM:
    def __init__(self, model, temperature, timeout, max_retries):
        self.model = model
        self.temperature = temperature
        self.timeout = timeout
        self.max_retries = max_retries

    def invoke(self, messages):
        return AIMessage(content=f"mock:{self.model}")


def test_production_agent_invoke_with_mock_llm(monkeypatch):
    monkeypatch.setattr(
        "app.agent.get_settings",
        lambda: types.SimpleNamespace(
            primary_model="mock-primary",
            fallback_model="mock-fallback",
            max_retries=1,
        ),
    )
    monkeypatch.setattr("app.agent.ChatOpenAI", FakeLLM)

    agent = ProductionAgent()
    result = agent.invoke("hello")

    assert result["response"] == "mock:mock-primary"
    assert result["model_used"] == "primary"
    assert result["error"] is None
