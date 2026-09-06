import pytest

from backend.services import diagnosis_service


@pytest.fixture(autouse=True)
def isolate_provider(monkeypatch):
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    diagnosis_service.reset_provider()
    yield
    diagnosis_service.reset_provider()
