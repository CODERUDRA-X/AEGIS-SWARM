"""
AEGIS-SWARM :: Test Suite
===========================
WHY THESE TESTS EXIST (design decision):
Each test targets a specific security or behavioral guarantee of the system.
Tests are grouped by what they protect against:
  - Security tests: validate that attack vectors are rejected at the API boundary
  - Unit tests: validate internal helper logic in isolation
  - Integration smoke tests: validate the pipeline structure without hitting real APIs

Run with: pytest test_main.py -v
"""

import io
import json
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from server import app, safe_json_parse

client = TestClient(app)


# ─────────────────────────────────────────────
# SECURITY TESTS
# These verify that the API boundary rejects
# malformed or malicious inputs before any
# agent logic is invoked.
# ─────────────────────────────────────────────

def test_rejects_wrong_http_method():
    """
    The /api/analyze endpoint must only accept POST.
    A GET request must return 405 Method Not Allowed.
    This ensures the attack surface is minimal -- read-only probes
    cannot trigger agent execution.
    """
    response = client.get("/api/analyze")
    assert response.status_code == 405


def test_rejects_non_image_file_type():
    """
    File type validation must block non-image uploads (e.g., .txt, .pdf, .exe).
    An attacker should not be able to pass arbitrary data into the vision agent.
    Expected: 400 Bad Request with a clear error message.
    """
    files = {"file": ("malicious.txt", b"fake text payload", "text/plain")}
    response = client.post("/api/analyze", files=files)
    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]


def test_rejects_pdf_disguised_as_image():
    """
    Content-type spoofing check: even if the attacker names a file "photo.jpg"
    but sends it with a PDF MIME type, it must be rejected.
    The guard is on content_type, not file extension.
    """
    files = {"file": ("photo.jpg", b"%PDF-1.4 fake pdf content", "application/pdf")}
    response = client.post("/api/analyze", files=files)
    assert response.status_code == 400


def test_rejects_oversized_file():
    """
    File size enforcement: files exceeding MAX_FILE_SIZE (5MB) must be rejected
    with 413 Request Entity Too Large.
    This prevents memory exhaustion attacks via large uploads.
    """
    # Generate 6MB of fake image data (exceeds the 5MB limit)
    oversized_data = b"\xff\xd8\xff" + b"A" * (6 * 1024 * 1024)
    files = {"file": ("big_image.jpg", oversized_data, "image/jpeg")}
    response = client.post("/api/analyze", files=files)
    assert response.status_code == 413


# ─────────────────────────────────────────────
# UNIT TESTS: safe_json_parse()
# This helper is the crash-prevention layer
# between LLM responses and the rest of the
# pipeline. It must handle every failure mode
# gracefully.
# ─────────────────────────────────────────────

def test_safe_json_parse_valid_input():
    """
    Normal case: valid JSON string must be parsed into a Python dict correctly.
    """
    raw = '{"threat_level": "HIGH", "reason": "Dense crowd on stairs."}'
    result = safe_json_parse(raw, {"threat_level": "STANDBY"})
    assert result["threat_level"] == "HIGH"
    assert result["reason"] == "Dense crowd on stairs."


def test_safe_json_parse_strips_markdown_fences():
    """
    LLMs frequently wrap JSON in markdown code fences (```json ... ```).
    safe_json_parse must strip these before parsing.
    Without this, json.loads() would raise a JSONDecodeError and the
    entire pipeline would fall back to the default, losing real data.
    """
    raw = '```json\n{"threat_level": "MEDIUM", "reason": "Open area."}\n```'
    result = safe_json_parse(raw, {"threat_level": "STANDBY"})
    assert result["threat_level"] == "MEDIUM"


def test_safe_json_parse_returns_fallback_on_garbage():
    """
    If the LLM returns completely unparseable text (model error, timeout fragment,
    partial response), safe_json_parse must return the provided fallback dict
    rather than raising an exception and crashing the pipeline.
    """
    raw = "Sorry, I cannot process this request right now."
    fallback = {"threat_level": "STANDBY", "reason": "Parse failure."}
    result = safe_json_parse(raw, fallback)
    assert result["threat_level"] == "STANDBY"


def test_safe_json_parse_returns_fallback_on_empty_string():
    """
    Edge case: empty string input (e.g., API timeout returning no body).
    Must return fallback, not raise.
    """
    result = safe_json_parse("", {"threat_level": "STANDBY"})
    assert result["threat_level"] == "STANDBY"
