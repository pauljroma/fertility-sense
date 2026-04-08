"""Security tests: config, auth, CORS, and credential validation."""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from fertility_sense.auth import set_config
from fertility_sense.config import FertilitySenseConfig


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


class TestConfig:
    def test_defaults(self):
        cfg = FertilitySenseConfig()
        assert cfg.host == "127.0.0.1"
        assert cfg.port == 9300
        assert cfg.api_key == ""

    def test_loads_from_env(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("FERTILITY_SENSE_HOST", "0.0.0.0")
        monkeypatch.setenv("FERTILITY_SENSE_PORT", "8080")
        monkeypatch.setenv("FERTILITY_SENSE_API_KEY", "test-key-123")
        cfg = FertilitySenseConfig()
        assert cfg.host == "0.0.0.0"
        assert cfg.port == 8080
        assert cfg.api_key == "test-key-123"

    def test_port_validation_too_high(self):
        with pytest.raises(ValidationError):
            FertilitySenseConfig(port=70000)

    def test_port_validation_zero(self):
        with pytest.raises(ValidationError):
            FertilitySenseConfig(port=0)

    def test_port_validation_negative(self):
        with pytest.raises(ValidationError):
            FertilitySenseConfig(port=-1)


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------


def _make_client(api_key: str = "secret-key") -> TestClient:
    """Create a test client with a given API key configured."""
    from fertility_sense.api import create_app

    cfg = FertilitySenseConfig(api_key=api_key)
    application = create_app(cfg)
    return TestClient(application)


class TestAuth:
    def test_health_no_auth_required(self):
        client = _make_client()
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_returns_401_without_token(self):
        client = _make_client()
        resp = client.get("/agents")
        assert resp.status_code == 401
        body = resp.json()
        assert body["detail"]["error"] == "missing_token"

    def test_returns_401_with_wrong_token(self):
        client = _make_client()
        resp = client.get("/agents", headers={"Authorization": "Bearer wrong-key"})
        assert resp.status_code == 401
        body = resp.json()
        assert body["detail"]["error"] == "invalid_token"

    def test_passes_with_valid_token(self):
        client = _make_client()
        resp = client.get("/agents", headers={"Authorization": "Bearer secret-key"})
        assert resp.status_code == 200

    def test_no_auth_when_key_empty(self):
        """When api_key is empty string, auth is effectively disabled."""
        client = _make_client(api_key="")
        resp = client.get("/agents")
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------


class TestCORS:
    def test_cors_headers_present(self):
        from fertility_sense.api import create_app

        cfg = FertilitySenseConfig(cors_origins=["http://localhost:3000"])
        application = create_app(cfg)
        client = TestClient(application)
        resp = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert "access-control-allow-origin" in resp.headers

    def test_cors_rejects_unlisted_origin(self):
        from fertility_sense.api import create_app

        cfg = FertilitySenseConfig(cors_origins=["http://localhost:3000"])
        application = create_app(cfg)
        client = TestClient(application)
        resp = client.options(
            "/health",
            headers={
                "Origin": "http://evil.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        # CORSMiddleware does not set allow-origin for disallowed origins
        assert resp.headers.get("access-control-allow-origin") != "http://evil.com"


# ---------------------------------------------------------------------------
# Reddit feed credential validation
# ---------------------------------------------------------------------------


class TestRedditCredentials:
    def test_raises_on_empty_client_id(self):
        cfg = FertilitySenseConfig(reddit_client_id="", reddit_client_secret="secret")
        with pytest.raises(ValueError, match="Reddit client ID is required"):
            from fertility_sense.feeds.reddit import RedditFeed

            RedditFeed(config=cfg)

    def test_raises_on_empty_client_secret(self):
        cfg = FertilitySenseConfig(reddit_client_id="my-id", reddit_client_secret="")
        with pytest.raises(ValueError, match="Reddit client secret is required"):
            from fertility_sense.feeds.reddit import RedditFeed

            RedditFeed(config=cfg)

    def test_accepts_valid_credentials(self):
        cfg = FertilitySenseConfig(
            reddit_client_id="my-id", reddit_client_secret="my-secret"
        )
        from fertility_sense.feeds.reddit import RedditFeed

        feed = RedditFeed(config=cfg)
        assert feed._client_id == "my-id"
        assert feed._client_secret == "my-secret"
