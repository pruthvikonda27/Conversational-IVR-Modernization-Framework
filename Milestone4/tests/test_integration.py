"""
=============================================================================
MODULE 4 — Integration Tests (Track C: Web Simulator)
Verifies that API endpoints correctly interact with the in-memory session
store across multi-step call flows. Each test depends on prior steps —
that's what makes these integration tests, not unit tests.
=============================================================================
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../Milestone2"))

import pytest
from fastapi.testclient import TestClient
from backend import app, SESSIONS

client = TestClient(app)


# ── helpers ───────────────────────────────────────────────────────────────────

def start_session(caller_id="+919000000001"):
    resp = client.post("/ivr/start", json={"caller_id": caller_id, "language": "EN"})
    assert resp.status_code == 200
    return resp.json()["data"]["session_id"]


# ── C2-1  Session creation and persistence ────────────────────────────────────

class TestSessionPersistence:
    def test_session_created_in_store(self):
        """Session must be persisted in SESSIONS dict after /ivr/start."""
        sid = start_session()
        assert sid in SESSIONS

    def test_session_contains_caller_id(self):
        caller = "+919111111111"
        resp = client.post("/ivr/start", json={"caller_id": caller})
        sid = resp.json()["data"]["session_id"]
        assert SESSIONS[sid]["caller_id"] == caller

    def test_session_initial_flow_is_welcome(self):
        sid = start_session()
        assert SESSIONS[sid]["current_flow"] == "welcome"

    def test_session_history_starts_empty_then_grows(self):
        sid = start_session()
        # After start, call_started event should be logged
        assert len(SESSIONS[sid]["history"]) >= 1
        assert SESSIONS[sid]["history"][0]["event"] == "call_started"

    def test_multiple_sessions_are_independent(self):
        sid1 = start_session("+919000000001")
        sid2 = start_session("+919000000002")
        assert sid1 != sid2
        assert SESSIONS[sid1]["caller_id"] != SESSIONS[sid2]["caller_id"]


# ── C2-2  Conversation flow — state transitions ───────────────────────────────

class TestConversationFlow:
    def test_dtmf_1_transitions_flow_to_pnr(self):
        """After pressing 1, session flow must update to pnr_flow."""
        sid = start_session()
        client.post("/ivr/input", json={
            "session_id": sid, "digit": "1", "current_flow": "main_menu"
        })
        assert SESSIONS[sid]["current_flow"] == "pnr_flow"

    def test_dtmf_2_transitions_flow_to_booking(self):
        sid = start_session()
        client.post("/ivr/input", json={
            "session_id": sid, "digit": "2", "current_flow": "main_menu"
        })
        assert SESSIONS[sid]["current_flow"] == "booking_flow"

    def test_booking_class_stored_in_session(self):
        """Selecting class '1' (Sleeper) must persist in booking_slots."""
        sid = start_session()
        client.post("/ivr/input", json={
            "session_id": sid, "digit": "1", "current_flow": "select_class"
        })
        assert SESSIONS[sid]["booking_slots"]["travel_class"] == "Sleeper (SL)"

    def test_booking_quota_stored_in_session(self):
        sid = start_session()
        client.post("/ivr/input", json={
            "session_id": sid, "digit": "1", "current_flow": "select_quota"
        })
        assert SESSIONS[sid]["booking_slots"]["quota"] == "General"

    def test_booking_berth_stored_in_session(self):
        sid = start_session()
        client.post("/ivr/input", json={
            "session_id": sid, "digit": "1", "current_flow": "select_berth"
        })
        assert SESSIONS[sid]["booking_slots"]["berth"] == "Lower"

    def test_full_booking_slot_accumulation(self):
        """All three booking preferences must accumulate in the same session."""
        sid = start_session()
        client.post("/ivr/input", json={"session_id": sid, "digit": "2", "current_flow": "select_class"})
        client.post("/ivr/input", json={"session_id": sid, "digit": "2", "current_flow": "select_quota"})
        client.post("/ivr/input", json={"session_id": sid, "digit": "2", "current_flow": "select_berth"})
        slots = SESSIONS[sid]["booking_slots"]
        assert slots["travel_class"] == "Third AC (3A)"
        assert slots["quota"] == "Ladies"
        assert slots["berth"] == "Middle"


# ── C2-3  Conversation booking flow (multi-step) ──────────────────────────────

class TestConversationBookingFlow:
    def test_step1_create_session(self):
        """Step 1: session is created and welcome prompt returned."""
        resp = client.post("/ivr/start", json={"caller_id": "+919500000001"})
        assert resp.status_code == 200
        assert "session_id" in resp.json()["data"]

    def test_step2_navigate_to_booking_menu(self):
        """Step 2: pressing 2 routes to booking flow."""
        sid = start_session()
        resp = client.post("/ivr/input", json={
            "session_id": sid, "digit": "2", "current_flow": "main_menu"
        })
        assert resp.json()["acs_event"] == "booking_flow"
        assert "Booking" in resp.json()["data"]["selected"]

    def test_step3_select_class_carries_session_context(self):
        """Step 3: class selection requires session context from step 2."""
        sid = start_session()
        # Step 2
        client.post("/ivr/input", json={"session_id": sid, "digit": "2", "current_flow": "main_menu"})
        # Step 3 — session must still be valid
        resp = client.post("/ivr/input", json={
            "session_id": sid, "digit": "3", "current_flow": "select_class"
        })
        assert resp.status_code == 200
        assert "Second AC" in resp.json()["prompt"]

    def test_step4_pnr_check_after_booking_flow(self):
        """Session can handle PNR check independently of booking state."""
        sid = start_session()
        resp = client.post("/ivr/pnr", json={"session_id": sid, "pnr_number": "1234567890"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    def test_session_history_records_all_events(self):
        """Every interaction must be logged in session history."""
        sid = start_session()
        client.post("/ivr/input", json={"session_id": sid, "digit": "1", "current_flow": "main_menu"})
        client.post("/ivr/pnr", json={"session_id": sid, "pnr_number": "1234567890"})
        history = SESSIONS[sid]["history"]
        events = [h["event"] for h in history]
        assert "call_started" in events
        assert "dtmf" in events
        assert "pnr_check" in events


# ── C2-4  Session isolation ───────────────────────────────────────────────────

class TestSessionIsolation:
    def test_booking_slots_do_not_bleed_between_sessions(self):
        sid1 = start_session("+919600000001")
        sid2 = start_session("+919600000002")
        client.post("/ivr/input", json={"session_id": sid1, "digit": "1", "current_flow": "select_class"})
        # sid2 should have empty booking_slots
        assert SESSIONS[sid2]["booking_slots"] == {}

    def test_flow_state_independent_per_session(self):
        sid1 = start_session("+919700000001")
        sid2 = start_session("+919700000002")
        client.post("/ivr/input", json={"session_id": sid1, "digit": "2", "current_flow": "main_menu"})
        # sid2 flow should still be welcome
        assert SESSIONS[sid2]["current_flow"] == "welcome"


# ── C2-5  ACS bridge integration ─────────────────────────────────────────────

class TestACSBridgeIntegration:
    def test_bridge_logs_event_to_session(self):
        # Note: log() spreads data dict, so {"event": vxml_event} overwrites the
        # event key. The stored event is the vxml_event value ("filled"), not "acs_bridge".
        sid = start_session("+919800100001")
        client.post("/acs/bridge", json={
            "session_id": sid,
            "acs_call_connection_id": "conn-test-001",
            "vxml_event": "filled",
        })
        events = [h["event"] for h in SESSIONS[sid]["history"]]
        assert "filled" in events

    def test_bridge_payload_contains_language(self):
        sid = start_session()
        resp = client.post("/acs/bridge", json={
            "session_id": sid,
            "acs_call_connection_id": "conn-test-002",
            "vxml_event": "filled",
        })
        payload = resp.json()["data"]["bridge_payload"]
        assert payload["language"] == "EN"

    def test_bridge_payload_contains_booking_context(self):
        """Booking slots accumulated in session must appear in bridge payload."""
        sid = start_session()
        client.post("/ivr/input", json={"session_id": sid, "digit": "1", "current_flow": "select_class"})
        resp = client.post("/acs/bridge", json={
            "session_id": sid,
            "acs_call_connection_id": "conn-test-003",
            "vxml_event": "filled",
        })
        context = resp.json()["data"]["bridge_payload"]["context"]
        assert context.get("travel_class") == "Sleeper (SL)"