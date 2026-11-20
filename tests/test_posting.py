import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import app
from app.platforms.base import BasePlatform
from app.schemas import PlatformResult
from app.services import posting_service

VALID_MESSAGE = "Learn Python in 30 days! https://www.python.org/"


@pytest.fixture
def client(monkeypatch):
    for field_name in Settings.model_fields:
        monkeypatch.delenv(field_name.upper(), raising=False)

    app.dependency_overrides[get_settings] = lambda: Settings(_env_file=None)
    yield TestClient(app)
    app.dependency_overrides.clear()


class FakeSuccessPlatform(BasePlatform):
    name = "FakeOK"

    def is_configured(self) -> bool:
        return True

    async def publish(self, message: str) -> PlatformResult:
        return self._success("https://example.com/post/1", public_access=True)


class FakeCrashingPlatform(BasePlatform):
    name = "FakeCrash"

    def is_configured(self) -> bool:
        return True

    async def publish(self, message: str) -> PlatformResult:
        raise RuntimeError("API exploded")


def test_rejects_message_over_200_characters(client):
    response = client.post("/posting", json={"message": "a" * 190 + " https://example.com"})
    assert response.status_code == 422
    assert response.json()["errors"][0]["field"] == "message"


def test_rejects_message_without_link(client):
    response = client.post("/posting", json={"message": "No link here"})
    assert response.status_code == 422
    assert "No link was found" in response.json()["errors"][0]["message"]


def test_rejects_message_with_two_links(client):
    response = client.post("/posting", json={"message": "Two https://a.com and https://b.com"})
    assert response.status_code == 422
    assert "2 were found" in response.json()["errors"][0]["message"]


def test_rejects_invalid_url(client):
    response = client.post("/posting", json={"message": "Bad https://abc"})
    assert response.status_code == 422


def test_rejects_missing_message(client):
    response = client.post("/posting", json={})
    assert response.status_code == 422


def test_unconfigured_platforms_fail_cleanly(client):
    response = client.post("/posting", json={"message": VALID_MESSAGE})
    body = response.json()
    assert response.status_code == 200
    assert body["succeeded"] == 0
    assert all("Not configured" in r["error"] for r in body["results"])


def test_one_failure_does_not_stop_others(client, monkeypatch):
    monkeypatch.setattr(
        posting_service,
        "PLATFORM_CLASSES",
        [FakeSuccessPlatform, FakeCrashingPlatform, FakeSuccessPlatform],
    )
    body = client.post("/posting", json={"message": VALID_MESSAGE}).json()

    assert body["total_platforms"] == 3
    assert body["succeeded"] == 2
    assert body["failed"] == 1
    assert body["results"][1]["status"] == "failed"
    assert "API exploded" in body["results"][1]["error"]
    assert body["results"][0]["posted_at"] is not None