import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _spec(**overrides):
    spec = {
        "title": "Q3 Board Update",
        "format": "html",
        "sections": [
            {"heading": "Summary", "content": "Revenue grew 12% quarter over quarter."},
            {"heading": "Risks", "content": "Churn ticked up in the SMB segment."},
        ],
    }
    spec.update(overrides)
    return spec


def test_html_end_to_end():
    resp = client.post("/v1/artifacts", json=_spec())
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "stored"
    assert body["url"].endswith(".html")
    assert body["qa"]["passed"] is True

    fetched = client.get(body["url"].replace("http://localhost:8090", ""))
    assert fetched.status_code == 200
    assert "Q3 Board Update" in fetched.text
    assert "Revenue grew 12%" in fetched.text


def test_markdown_end_to_end():
    resp = client.post("/v1/artifacts", json=_spec(format="markdown"))
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "stored"
    assert body["url"].endswith(".md")


def test_stub_format_reports_not_connected():
    resp = client.post("/v1/artifacts", json=_spec(format="pptx"))
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "stub_not_connected"
    assert body["url"] is None


def test_invalid_spec_rejected():
    resp = client.post("/v1/artifacts", json=_spec(sections=[]))
    assert resp.status_code == 422


def test_duplicate_headings_rejected():
    resp = client.post(
        "/v1/artifacts",
        json=_spec(
            sections=[
                {"heading": "Summary", "content": "a"},
                {"heading": "Summary", "content": "b"},
            ]
        ),
    )
    assert resp.status_code == 422


def test_html_content_is_escaped_not_interpreted():
    resp = client.post(
        "/v1/artifacts",
        json=_spec(
            sections=[{"heading": "Notes", "content": "<script>alert(1)</script>"}]
        ),
    )
    body = resp.json()
    fetched = client.get(body["url"].replace("http://localhost:8090", ""))
    assert "<script>" not in fetched.text
    assert "&lt;script&gt;" in fetched.text
