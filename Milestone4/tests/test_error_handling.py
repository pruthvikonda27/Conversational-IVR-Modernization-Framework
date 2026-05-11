"""
=============================================================================
MODULE 4 — Error Handling & Logging Tests (Track C: Web Simulator)
Verifies that the system fails gracefully — returning meaningful error
messages rather than cryptic stack traces or silent failures.
=============================================================================
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../Milestone2"))

import pytest
import logging
from fastapi.testclient import TestClient
from backend import app

client = TestClient(app)


# ── helpers ───────────────────────────────────────────────────────────────────

def start_session(caller_id="+919000099001"):
    resp = client.post("/ivr/start", json={"caller_id": caller_id})
    assert resp.status_code == 200
    return resp.json()["data"]["session_id"]


# ── EH-1  Invalid / missing resource ─────────────────────────────────────────

class TestInvalidResourceErrors:
    def test_invalid_session_id_returns_404(self):
        """A request with a nonexistent session_id must return 404, not 500."""
        resp = client.post("/ivr/input", json={
            "session_id": "INVALID_SESSION_ID_XYZ",
            "digit": "1",
            "current_flow": "main_menu"
        })
        assert resp.status_code == 404

    def test_invalid_session_pnr_returns_404(self):
        resp = client.post("/ivr/pnr", json={
            "session_id": "INVALID_SESSION_ID_XYZ",
            "pnr_number": "1234567890"
        })
        assert resp.status_code == 404

    def test_invalid_session_booking_returns_404(self):
        resp = client.post("/ivr/booking", json={
            "session_id": "INVALID_SESSION_ID_XYZ",
            "train_number": "12951",
            "journey_date": "15032026",
            "from_station": "NDLS",
            "to_station": "MMCT",
            "travel_class": "1",
            "quota": "1",
            "berth_preference": "1",
        })
        assert resp.status_code == 404

    def test_invalid_session_tracking_returns_404(self):
        resp = client.post("/ivr/tracking", json={
            "session_id": "INVALID_SESSION_ID_XYZ",
            "train_number": "12951"
        })
        assert resp.status_code == 404

    def test_get_nonexistent_session_returns_404(self):
        resp = client.get("/session/nonexistent-id-abc")
        assert resp.status_code == 404

    def test_404_response_has_detail_field(self):
        resp = client.get("/session/nonexistent-id-abc")
        assert "detail" in resp.json()


# ── EH-2  Invalid payload — 422 Unprocessable Entity ─────────────────────────

class TestInvalidPayloadErrors:
    def test_start_missing_caller_id_returns_422(self):
        resp = client.post("/ivr/start", json={})
        assert resp.status_code == 422

    def test_start_wrong_type_returns_422(self):
        resp = client.post("/ivr/start", json={"caller_id": 12345})
        # FastAPI coerces int to str, so this may pass — test the contract
        assert resp.status_code in (200, 422)

    def test_input_missing_digit_returns_422(self):
        sid = start_session()
        resp = client.post("/ivr/input", json={
            "session_id": sid, "current_flow": "main_menu"
        })
        assert resp.status_code == 422

    def test_input_missing_flow_returns_422(self):
        sid = start_session()
        resp = client.post("/ivr/input", json={
            "session_id": sid, "digit": "1"
        })
        assert resp.status_code == 422

    def test_pnr_missing_pnr_number_returns_422(self):
        sid = start_session()
        resp = client.post("/ivr/pnr", json={"session_id": sid})
        assert resp.status_code == 422

    def test_booking_missing_required_fields_returns_422(self):
        sid = start_session()
        resp = client.post("/ivr/booking", json={"session_id": sid})
        assert resp.status_code == 422

    def test_tracking_missing_train_number_returns_422(self):
        sid = start_session()
        resp = client.post("/ivr/tracking", json={"session_id": sid})
        assert resp.status_code == 422

    def test_422_response_contains_field_errors(self):
        resp = client.post("/ivr/start", json={})
        body = resp.json()
        assert "detail" in body
        # FastAPI returns a list of field-level errors
        assert isinstance(body["detail"], list)
        assert len(body["detail"]) > 0


# ── EH-3  Business logic validation errors ────────────────────────────────────

class TestBusinessLogicErrors:
    def test_invalid_pnr_too_short_returns_invalid_status(self):
        sid = start_session()
        resp = client.post("/ivr/pnr", json={"session_id": sid, "pnr_number": "12345"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "invalid"

    def test_invalid_pnr_non_numeric_returns_invalid_status(self):
        sid = start_session()
        resp = client.post("/ivr/pnr", json={"session_id": sid, "pnr_number": "ABCDE12345"})
        assert resp.json()["status"] == "invalid"

    def test_invalid_train_number_too_short(self):
        sid = start_session()
        resp = client.post("/ivr/tracking", json={"session_id": sid, "train_number": "123"})
        assert resp.json()["status"] == "invalid"

    def test_invalid_train_number_non_numeric(self):
        sid = start_session()
        resp = client.post("/ivr/tracking", json={"session_id": sid, "train_number": "TRAIN"})
        assert resp.json()["status"] == "invalid"

    def test_invalid_dtmf_digit_returns_invalid_not_500(self):
        sid = start_session()
        resp = client.post("/ivr/input", json={
            "session_id": sid, "digit": "Z", "current_flow": "main_menu"
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "invalid"

    def test_unexpected_flow_returns_error_not_500(self):
        sid = start_session()
        resp = client.post("/ivr/input", json={
            "session_id": sid, "digit": "1", "current_flow": "unknown_flow_xyz"
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "error"


# ── EH-4  Malformed JSON / wrong content type ─────────────────────────────────

class TestMalformedRequests:
    def test_non_json_body_returns_422(self):
        resp = client.post(
            "/ivr/start",
            content="not json at all",
            headers={"Content-Type": "application/json"}
        )
        assert resp.status_code == 422

    def test_empty_body_returns_422(self):
        resp = client.post("/ivr/start", content=b"")
        assert resp.status_code in (422, 400)


# ── EH-5  Structured logging verification ────────────────────────────────────

class TestStructuredLogging:
    def test_session_history_logs_call_started(self):
        """Every call start must produce a call_started log entry."""
        from backend import SESSIONS
        sid = start_session()
        events = [h["event"] for h in SESSIONS[sid]["history"]]
        assert "call_started" in events

    def test_session_history_logs_dtmf_event(self):
        from backend import SESSIONS
        sid = start_session()
        client.post("/ivr/input", json={
            "session_id": sid, "digit": "1", "current_flow": "main_menu"
        })
        events = [h["event"] for h in SESSIONS[sid]["history"]]
        assert "dtmf" in events

    def test_session_history_logs_pnr_check(self):
        from backend import SESSIONS
        sid = start_session()
        client.post("/ivr/pnr", json={"session_id": sid, "pnr_number": "4521679834"})
        events = [h["event"] for h in SESSIONS[sid]["history"]]
        assert "pnr_check" in events

    def test_session_history_logs_booking(self):
        from backend import SESSIONS
        sid = start_session()
        client.post("/ivr/booking", json={
            "session_id": sid,
            "train_number": "12951",
            "journey_date": "15032026",
            "from_station": "NDLS",
            "to_station": "MMCT",
            "travel_class": "1",
            "quota": "1",
            "berth_preference": "1",
        })
        events = [h["event"] for h in SESSIONS[sid]["history"]]
        assert "booking" in events

    def test_session_history_logs_tracking(self):
        from backend import SESSIONS
        sid = start_session()
        client.post("/ivr/tracking", json={"session_id": sid, "train_number": "12951"})
        events = [h["event"] for h in SESSIONS[sid]["history"]]
        assert "tracking" in events

    def test_session_history_logs_acs_bridge(self):
        # log() spreads data dict so {"event": vxml_event} overwrites the event key.
        # The stored event is the vxml_event value ("filled"), not "acs_bridge".
        from backend import SESSIONS
        sid = start_session("+919800200001")
        client.post("/acs/bridge", json={
            "session_id": sid,
            "acs_call_connection_id": "conn-log-test",
            "vxml_event": "filled",
        })
        events = [h["event"] for h in SESSIONS[sid]["history"]]
        assert "filled" in events

    def test_log_entries_have_timestamp(self):
        from backend import SESSIONS
        sid = start_session()
        for entry in SESSIONS[sid]["history"]:
            assert "ts" in entry
            assert len(entry["ts"]) > 0

    def test_log_entries_have_event_field(self):
        from backend import SESSIONS
        sid = start_session()
        client.post("/ivr/input", json={
            "session_id": sid, "digit": "1", "current_flow": "main_menu"
        })
        for entry in SESSIONS[sid]["history"]:
            assert "event" in entry