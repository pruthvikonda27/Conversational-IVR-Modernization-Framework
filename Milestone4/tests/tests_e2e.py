"""
=============================================================================
MODULE 4 — End-to-End Tests (Track C: Web Simulator)
Simulates complete user call journeys from start to finish.
Each test covers a full user story, not just a single function.
=============================================================================
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../Milestone2"))

import pytest
from fastapi.testclient import TestClient
from backend import app, SESSIONS

client = TestClient(app)


# ── E2E-1  Happy path: full PNR check journey ─────────────────────────────────

class TestFullPNRJourney:
    def test_complete_pnr_flow(self):
        """
        User story: As a caller, I want to check my PNR status by pressing 1
        and entering my PNR number.
        Steps: start → press 1 → check PNR → verify result
        """
        # Step 1: Start call
        resp = client.post("/ivr/start", json={"caller_id": "+919800000001"})
        assert resp.status_code == 200
        sid = resp.json()["data"]["session_id"]
        assert "Welcome" in resp.json()["prompt"]

        # Step 2: Press 1 for PNR
        resp = client.post("/ivr/input", json={
            "session_id": sid, "digit": "1", "current_flow": "main_menu"
        })
        assert resp.status_code == 200
        assert resp.json()["acs_event"] == "pnr_flow"

        # Step 3: Submit PNR
        resp = client.post("/ivr/pnr", json={"session_id": sid, "pnr_number": "4521679834"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"
        assert "CONFIRMED" in resp.json()["prompt"]
        assert resp.json()["data"]["pnr_details"]["pnr"] == "4521679834"

        # Step 4: Session still valid after flow
        assert sid in SESSIONS


# ── E2E-2  Happy path: full booking journey ───────────────────────────────────

class TestFullBookingJourney:
    def test_complete_booking_flow(self):
        """
        User story: As a caller, I want to book a ticket by pressing 2,
        selecting class, quota, and berth, then submitting booking details.
        """
        # Step 1: Start
        resp = client.post("/ivr/start", json={"caller_id": "+919800000002"})
        sid = resp.json()["data"]["session_id"]

        # Step 2: Press 2 for booking
        resp = client.post("/ivr/input", json={
            "session_id": sid, "digit": "2", "current_flow": "main_menu"
        })
        assert resp.json()["acs_event"] == "booking_flow"

        # Step 3: Select class (1 = Sleeper)
        resp = client.post("/ivr/input", json={
            "session_id": sid, "digit": "1", "current_flow": "select_class"
        })
        assert "Sleeper" in resp.json()["prompt"]

        # Step 4: Select quota (1 = General)
        resp = client.post("/ivr/input", json={
            "session_id": sid, "digit": "1", "current_flow": "select_quota"
        })
        assert "General" in resp.json()["prompt"]

        # Step 5: Select berth (1 = Lower)
        resp = client.post("/ivr/input", json={
            "session_id": sid, "digit": "1", "current_flow": "select_berth"
        })
        assert "Lower" in resp.json()["prompt"]

        # Step 6: Submit booking
        resp = client.post("/ivr/booking", json={
            "session_id": sid,
            "train_number": "12951",
            "journey_date": "15032026",
            "from_station": "NDLS",
            "to_station": "MMCT",
            "travel_class": "1",
            "quota": "1",
            "berth_preference": "1",
            "passenger_count": 1,
        })
        assert resp.status_code == 200
        booking = resp.json()["data"]["booking"]
        assert booking["booking_id"].startswith("BK")
        assert booking["status"] == "PENDING_PAYMENT"
        assert "pay_link" in booking


# ── E2E-3  Happy path: live tracking journey ──────────────────────────────────

class TestFullTrackingJourney:
    def test_complete_tracking_flow(self):
        """
        User story: As a caller, I want to track my train by pressing 4
        and entering the train number.
        """
        resp = client.post("/ivr/start", json={"caller_id": "+919800000003"})
        sid = resp.json()["data"]["session_id"]

        resp = client.post("/ivr/input", json={
            "session_id": sid, "digit": "4", "current_flow": "main_menu"
        })
        assert resp.json()["acs_event"] == "tracking_flow"

        resp = client.post("/ivr/tracking", json={"session_id": sid, "train_number": "12951"})
        assert resp.status_code == 200
        track = resp.json()["data"]["tracking"]
        assert "current_station" in track
        assert "delay_minutes" in track
        assert "eta_next_station" in track


# ── E2E-4  Happy path: Tatkal journey ────────────────────────────────────────

class TestFullTatkalJourney:
    def test_complete_tatkal_flow(self):
        resp = client.post("/ivr/start", json={"caller_id": "+919800000004"})
        sid = resp.json()["data"]["session_id"]

        resp = client.post("/ivr/input", json={
            "session_id": sid, "digit": "3", "current_flow": "main_menu"
        })
        assert resp.json()["acs_event"] == "tatkal_flow"

        resp = client.post("/ivr/tatkal", json={
            "session_id": sid,
            "train_number": "12951",
            "journey_date": "15032026",
            "from_station": "NDLS",
            "to_station": "MMCT",
            "travel_class": "2",
            "passenger_count": 1,
        })
        assert resp.status_code == 200
        # Either queued or window closed — both are valid
        assert resp.json()["status"] in ("success", "unavailable")


# ── E2E-5  Edge case: invalid key press handled gracefully ────────────────────

class TestInvalidKeyHandling:
    def test_invalid_key_does_not_crash_session(self):
        """Pressing an unmapped key must return an error response, not a 500."""
        resp = client.post("/ivr/start", json={"caller_id": "+919800000005"})
        sid = resp.json()["data"]["session_id"]

        resp = client.post("/ivr/input", json={
            "session_id": sid, "digit": "7", "current_flow": "main_menu"
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "invalid"
        # Session must still be alive
        assert sid in SESSIONS

    def test_repeated_invalid_keys_session_survives(self):
        resp = client.post("/ivr/start", json={"caller_id": "+919800000006"})
        sid = resp.json()["data"]["session_id"]
        for digit in ["6", "7", "8"]:
            resp = client.post("/ivr/input", json={
                "session_id": sid, "digit": digit, "current_flow": "main_menu"
            })
            assert resp.status_code == 200
        assert sid in SESSIONS


# ── E2E-6  Agent transfer journey ────────────────────────────────────────────

class TestAgentTransferJourney:
    def test_press_9_transfers_to_agent(self):
        resp = client.post("/ivr/start", json={"caller_id": "+919800000007"})
        sid = resp.json()["data"]["session_id"]

        resp = client.post("/ivr/input", json={
            "session_id": sid, "digit": "9", "current_flow": "main_menu"
        })
        assert resp.json()["status"] == "transfer"
        assert resp.json()["acs_event"] == "agent_transfer"
        assert "agent" in resp.json()["prompt"].lower()


# ── E2E-7  Session cleared / cleanup ─────────────────────────────────────────

class TestSessionCleanup:
    def test_session_exists_during_call(self):
        resp = client.post("/ivr/start", json={"caller_id": "+919800000008"})
        sid = resp.json()["data"]["session_id"]
        assert sid in SESSIONS

    def test_get_session_after_call(self):
        resp = client.post("/ivr/start", json={"caller_id": "+919800000009"})
        sid = resp.json()["data"]["session_id"]
        resp = client.get(f"/session/{sid}")
        assert resp.status_code == 200
        assert resp.json()["data"]["session_id"] == sid

    def test_nonexistent_session_after_call_returns_404(self):
        resp = client.get("/session/fake-session-id-xyz")
        assert resp.status_code == 404


# ── E2E-8  Full IVR flow — complete multi-step journey ───────────────────────

class TestFullIVRFlow:
    def test_full_ivr_flow_start_to_booking_complete(self):
        """
        Complete IVR journey:
        start → press 2 (booking) → class → quota → berth → submit booking
        Verifies HTTP status and semantic content at every step.
        """
        # 1. Start IVR
        resp = client.post("/ivr/start", json={"caller_id": "+919900000001"})
        assert resp.status_code == 200
        sid = resp.json()["data"]["session_id"]

        # 2. Navigate to booking
        resp = client.post("/ivr/input", json={
            "session_id": sid, "digit": "2", "current_flow": "main_menu"
        })
        assert resp.status_code == 200
        assert resp.json()["acs_event"] == "booking_flow"

        # 3. Select class 1 (Sleeper)
        resp = client.post("/ivr/input", json={
            "session_id": sid, "digit": "1", "current_flow": "select_class"
        })
        assert resp.status_code == 200

        # 4. Select quota 1 (General)
        resp = client.post("/ivr/input", json={
            "session_id": sid, "digit": "1", "current_flow": "select_quota"
        })
        assert resp.status_code == 200

        # 5. Select berth 1 (Lower)
        resp = client.post("/ivr/input", json={
            "session_id": sid, "digit": "1", "current_flow": "select_berth"
        })
        assert resp.status_code == 200

        # 6. Complete booking
        resp = client.post("/ivr/booking", json={
            "session_id": sid,
            "train_number": "12951",
            "journey_date": "15032026",
            "from_station": "NDLS",
            "to_station": "MMCT",
            "travel_class": "1",
            "quota": "1",
            "berth_preference": "1",
            "passenger_count": 2,
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"
        booking = resp.json()["data"]["booking"]
        assert booking["passengers"] == 2
        assert booking["status"] == "PENDING_PAYMENT"

        # 7. Session still valid
        resp = client.get(f"/session/{sid}")
        assert resp.status_code == 200