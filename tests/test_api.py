from __future__ import annotations

import os
from fastapi.testclient import TestClient

from api.app import app


def test_health():
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_recommend_requires_api_key():
    client = TestClient(app)
    r = client.get("/recommend/1")
    assert r.status_code == 401