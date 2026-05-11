"""
=============================================================================
PROJECT   : Conversational IVR Modernization Framework
MODULE    : Module 2 — Integration Layer Development
MILESTONE : Milestone 2 | IRCTC Smart IVR System (Modern UI Version)
=============================================================================
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from pathlib import Path
import uuid, os

app = FastAPI(
    title="IRCTC Smart IVR — Modern Integration Layer",
    description="Milestone 2: FastAPI middleware connecting VXML IVR to ACS/BAP.",
    version="2.0.0",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

SESSIONS: dict = {}

MAIN_MENU = {
    "1": {"service": "PNR Status Check",         "acs_event": "pnr_flow",       "collect": "pnr_number"},
    "2": {"service": "Smart Ticket Booking",      "acs_event": "booking_flow",   "collect": "journey_details"},
    "3": {"service": "Tatkal Emergency Booking",  "acs_event": "tatkal_flow",    "collect": "tatkal_details"},
    "4": {"service": "Live Train Tracking",       "acs_event": "tracking_flow",  "collect": "train_number"},
    "5": {"service": "Cancel & Refund",           "acs_event": "cancel_flow",    "collect": "pnr_number"},
    "9": {"service": "Talk to Agent",             "acs_event": "agent_transfer", "collect": None},
    "0": {"service": "Repeat Menu",               "acs_event": "repeat_menu",    "collect": None},
}

BOOKING_CLASS    = {"1": "Sleeper (SL)", "2": "Third AC (3A)", "3": "Second AC (2A)", "4": "First AC (1A)", "5": "Chair Car (CC)"}
BOOKING_QUOTA    = {"1": "General", "2": "Ladies", "3": "Senior Citizen", "4": "Defence", "5": "Tourist"}
BERTH_PREF       = {"1": "Lower", "2": "Middle", "3": "Upper", "4": "Side Lower", "5": "Side Upper", "6": "No Preference"}

class StartRequest(BaseModel):
    caller_id: str
    language: Optional[str] = "EN"
    acs_call_connection_id: Optional[str] = None

class DTMFRequest(BaseModel):
    session_id: str
    digit: str
    current_flow: str
    acs_recognize_result: Optional[dict] = None

class PNRRequest(BaseModel):
    session_id: str
    pnr_number: str

class BookingRequest(BaseModel):
    session_id: str
    train_number: str
    journey_date: str
    from_station: str
    to_station: str
    travel_class: str
    quota: str
    berth_preference: str
    passenger_count: Optional[int] = 1

class TatkalRequest(BaseModel):
    session_id: str
    train_number: str
    journey_date: str
    from_station: str
    to_station: str
    travel_class: str
    passenger_count: Optional[int] = 1

class TrackingRequest(BaseModel):
    session_id: str
    train_number: str
    journey_date: Optional[str] = None

class ACSBridgeRequest(BaseModel):
    session_id: str
    acs_call_connection_id: str
    vxml_event: str
    tts_text: Optional[str] = None
    collect_digits: Optional[bool] = False
    max_digits: Optional[int] = 1

def make_session(caller_id, language, acs_id):
    sid = str(uuid.uuid4())
    s = {
        "session_id": sid, "caller_id": caller_id,
        "language": language, "acs_call_connection_id": acs_id,
        "current_flow": "welcome", "booking_slots": {},
        "started_at": datetime.utcnow().isoformat(), "history": [],
    }
    SESSIONS[sid] = s
    return s

def get_session(sid):
    s = SESSIONS.get(sid)
    if not s:
        raise HTTPException(404, "Session not found or expired.")
    return s

def log(session, event, data):
    session["history"].append({"ts": datetime.utcnow().isoformat(), "event": event, **data})

def ok(prompt, data=None, acs_event="none", status="success"):
    return {"status": status, "timestamp": datetime.utcnow().isoformat(),
            "prompt": prompt, "acs_event": acs_event, "data": data or {}}

def _read_first_existing(paths):
    for ui_path in paths:
        if ui_path.exists():
            return ui_path.read_text(encoding="utf-8")
    return None


def _project_root_candidates(start_dir: Path):
    d = start_dir
    for _ in range(6):
        yield d
        if d.parent == d:
            break
        d = d.parent


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def serve_ui():
    base_dir = Path(__file__).resolve().parent
    roots = list(_project_root_candidates(base_dir))

    # Default to Milestone 3 conversational UI (matches Vercel screenshot style)
    m3_paths = []
    for r in roots:
        m3_paths.extend(
            [
                r / "Milestone3" / "irctc_m3.html",
                r / "milestone_3" / "irctc_m3.html",
            ]
        )
    m3_html = _read_first_existing(m3_paths)
    if m3_html is not None:
        return m3_html

    # Fallback to Milestone 2 UI when M3 is unavailable
    m2_paths = [base_dir / "ui.html"]
    for r in roots:
        m2_paths.extend(
            [
                r / "Milestone2" / "ui.html",
                r / "milestone_2" / "ui.html",
            ]
        )
    m2_html = _read_first_existing(m2_paths)
    if m2_html is not None:
        return m2_html

    raise HTTPException(status_code=500, detail="UI file not found. Expected M3 or M2 HTML files.")


@app.get("/m2", response_class=HTMLResponse, include_in_schema=False)
def serve_m2_ui():
    base_dir = Path(__file__).resolve().parent
    m2_paths = [
        base_dir / "ui.html",
        base_dir.parent / "Milestone2" / "ui.html",
        base_dir.parent / "milestone_2" / "ui.html",
    ]
    m2_html = _read_first_existing(m2_paths)
    if m2_html is not None:
        return m2_html
    raise HTTPException(status_code=500, detail="Milestone 2 UI not found.")

@app.post("/ivr/start", summary="Start IVR — Welcome Prompt")
def start_ivr(p: StartRequest):
    session = make_session(p.caller_id, p.language, p.acs_call_connection_id)
    log(session, "call_started", {"caller_id": p.caller_id})

    hour = (datetime.utcnow().hour + 5) % 24
    greet = "Suprabhat! Good Morning!" if hour < 12 else "Namaskar! Good Afternoon!" if hour < 17 else "Shubh Sandhya! Good Evening!"

    prompt = (
        f"{greet} Welcome to IRCTC Smart Railway Services. Aapka swagat hai. "
        "Press 1 for PNR Status. Press 2 for Smart Ticket Booking. "
        "Press 3 for Tatkal Emergency Booking. Press 4 for Live Train Tracking. "
        "Press 5 for Cancel and Refund. Press 9 to Talk to Agent. Press 0 to Repeat."
    )
    return ok(prompt, {
        "session_id": session["session_id"],
        "caller_id": p.caller_id,
        "menu": {k: v["service"] for k, v in MAIN_MENU.items()},
        "next_action": "collect_dtmf",
    }, "welcome_menu")

@app.post("/ivr/input", summary="DTMF Input Handler")
def handle_input(p: DTMFRequest):
    session = get_session(p.session_id)
    log(session, "dtmf", {"digit": p.digit, "flow": p.current_flow})

    if p.current_flow == "main_menu":
        if p.digit not in MAIN_MENU:
            return ok("Invalid option. Please press 1 to 5, 9 for agent, or 0 to repeat.",
                      {"valid_keys": list(MAIN_MENU.keys())}, "invalid_input", "invalid")
        sel = MAIN_MENU[p.digit]
        session["current_flow"] = sel["acs_event"]
        if p.digit == "9":
            return ok("Connecting you to an IRCTC support agent. Please hold. Dhanyavaad.",
                      {"transfer_queue": "irctc_support"}, "agent_transfer", "transfer")
        if p.digit == "0":
            session["current_flow"] = "main_menu"
            return ok("Repeating menu. Press 1 PNR, 2 Booking, 3 Tatkal, 4 Tracking, 5 Cancel, 9 Agent.",
                      {"session_id": p.session_id}, "repeat_menu")
        sub = _sub_prompt(p.digit)
        return ok(f"You selected {sel['service']}. {sub}",
                  {"selected": sel["service"], "next_collect": sel["collect"], "bap_flow": sel["acs_event"]},
                  sel["acs_event"])

    elif p.current_flow == "select_class":
        if p.digit not in BOOKING_CLASS:
            return ok("Invalid. Press 1 Sleeper, 2 Third AC, 3 Second AC, 4 First AC, 5 Chair Car.",
                      {}, "invalid_input", "invalid")
        session["booking_slots"]["travel_class"] = BOOKING_CLASS[p.digit]
        return ok(f"{BOOKING_CLASS[p.digit]} selected. Now choose quota: 1 General, 2 Ladies, 3 Senior Citizen, 4 Defence, 5 Tourist.",
                  {"travel_class": BOOKING_CLASS[p.digit]}, "collect_quota")

    elif p.current_flow == "select_quota":
        if p.digit not in BOOKING_QUOTA:
            return ok("Invalid quota. Press 1 to 5.", {}, "invalid_input", "invalid")
        session["booking_slots"]["quota"] = BOOKING_QUOTA[p.digit]
        return ok(f"{BOOKING_QUOTA[p.digit]} quota selected. Berth preference: 1 Lower, 2 Middle, 3 Upper, 4 Side Lower, 5 Side Upper, 6 No Preference.",
                  {"quota": BOOKING_QUOTA[p.digit]}, "collect_berth")

    elif p.current_flow == "select_berth":
        if p.digit not in BERTH_PREF:
            return ok("Invalid. Press 1 to 6.", {}, "invalid_input", "invalid")
        session["booking_slots"]["berth"] = BERTH_PREF[p.digit]
        return ok(f"{BERTH_PREF[p.digit]} berth selected. All preferences saved. Please enter your 5-digit train number.",
                  {"slots": session["booking_slots"], "bap_next": "confirm_booking"},
                  "collect_train_number")

    return ok("Unexpected flow. Please call back.", {"session_id": p.session_id}, "error", "error")

@app.post("/ivr/pnr", summary="PNR Status Check")
def check_pnr(p: PNRRequest):
    session = get_session(p.session_id)
    if len(p.pnr_number) != 10 or not p.pnr_number.isdigit():
        return ok("Invalid PNR. Please enter a valid 10-digit PNR number.",
                  {"session_id": p.session_id}, "invalid_pnr", "invalid")
    log(session, "pnr_check", {"pnr": p.pnr_number})
    data = {
        "pnr": p.pnr_number, "train": "12951 — Mumbai Rajdhani Express",
        "from": "NDLS (New Delhi)", "to": "MMCT (Mumbai Central)",
        "date": "15-Mar-2026", "class": "Third AC (3A)", "status": "CONFIRMED",
        "coach": "B4", "berth": "32 — Lower", "platform": "Platform 1",
        "departure": "16:55", "arrival": "08:35 +1",
    }
    prompt = (f"PNR {p.pnr_number}: CONFIRMED. Train {data['train']}. "
              f"From {data['from']} to {data['to']}. Coach {data['coach']}, Berth {data['berth']}. "
              f"Departs {data['departure']} from {data['platform']}. Shubh Yatra!")
    return ok(prompt, {"session_id": p.session_id, "pnr_details": data, "bap_card": "pnr_status_card"}, "pnr_delivered")

@app.post("/ivr/booking", summary="Smart Ticket Booking")
def smart_booking(p: BookingRequest):
    session = get_session(p.session_id)
    cls   = BOOKING_CLASS.get(p.travel_class, "Sleeper (SL)")
    quota = BOOKING_QUOTA.get(p.quota, "General")
    berth = BERTH_PREF.get(p.berth_preference, "No Preference")
    log(session, "booking", {"train": p.train_number, "class": cls})
    bid  = f"BK{uuid.uuid4().hex[:8].upper()}"
    fare = ({"1":450,"2":1200,"3":1850,"4":3200,"5":680}).get(p.travel_class, 450) * p.passenger_count
    booking = {
        "booking_id": bid, "train": p.train_number, "date": p.journey_date,
        "from": p.from_station.upper(), "to": p.to_station.upper(),
        "class": cls, "quota": quota, "berth": berth,
        "passengers": p.passenger_count, "fare": f"₹{fare}",
        "status": "PENDING_PAYMENT", "pay_link": f"https://irctc.co.in/pay/{bid}",
    }
    prompt = (f"Booking ID {bid} created. Train {p.train_number}, {cls}, {quota}. "
              f"Estimated fare ₹{fare} for {p.passenger_count} passenger. "
              "Payment link sent to registered mobile. Complete within 15 minutes. Dhanyavaad!")
    return ok(prompt, {"session_id": p.session_id, "booking": booking, "bap_next": "payment_flow"}, "booking_created")

@app.post("/ivr/tatkal", summary="Tatkal Emergency Booking")
def tatkal(p: TatkalRequest):
    session = get_session(p.session_id)
    hour = (datetime.utcnow().hour + 5) % 24
    if not (10 <= hour <= 23):
        return ok("Tatkal window closed. Opens at 10 AM IST for AC, 11 AM for Sleeper.",
                  {"opens_at": "10:00 AM IST"}, "tatkal_closed", "unavailable")
    log(session, "tatkal", {"train": p.train_number})
    surcharge = ({"1":200,"2":400,"3":500,"4":700,"5":300}).get(p.travel_class, 200) * p.passenger_count
    urgency   = min(100, (24 - hour) * 4 + p.passenger_count * 10)
    ref = f"TK{uuid.uuid4().hex[:6].upper()}"
    result = {
        "ref": ref, "train": p.train_number, "date": p.journey_date,
        "from": p.from_station.upper(), "to": p.to_station.upper(),
        "class": BOOKING_CLASS.get(p.travel_class,"SL"),
        "surcharge": f"₹{surcharge}", "urgency_score": urgency,
        "queue_position": max(1, 10 - urgency // 10), "status": "TATKAL_QUEUED",
    }
    prompt = (f"Tatkal booking initiated. Ref {ref}. Train {p.train_number}. "
              f"Surcharge ₹{surcharge}. Queue position {result['queue_position']}. "
              "SMS confirmation within 5 minutes. Tatkal booking guaranteed!")
    return ok(prompt, {"session_id": p.session_id, "tatkal": result}, "tatkal_queued")

@app.post("/ivr/tracking", summary="Live Train Tracking")
def tracking(p: TrackingRequest):
    session = get_session(p.session_id)
    if not p.train_number.isdigit() or len(p.train_number) != 5:
        return ok("Invalid train number. Please enter a 5-digit train number.",
                  {"session_id": p.session_id}, "invalid_train", "invalid")
    log(session, "tracking", {"train": p.train_number})
    track = {
        "train_number": p.train_number, "train_name": "Express Train",
        "current_station": "Mathura Junction (MTJ)",
        "next_station": "Agra Cantt (AGC)",
        "eta_next_station": "14:32", "last_updated": datetime.utcnow().isoformat(),
        "delay_minutes": 12, "delay_reason": "Signal clearance at Mathura",
        "distance_covered_km": 148, "total_distance_km": 1384,
        "on_time_score": "87%",
    }
    prompt = (f"Train {p.train_number} is currently at {track['current_station']}. "
              f"Running {track['delay_minutes']} minutes late due to {track['delay_reason']}. "
              f"Expected at {track['next_station']} by {track['eta_next_station']}. "
              f"On-time reliability score: {track['on_time_score']}. Safe journey!")
    return ok(prompt, {"session_id": p.session_id, "tracking": track, "bap_card": "train_tracker_card"}, "tracking_delivered")

@app.post("/acs/bridge", summary="ACS/BAP Connector Bridge")
def acs_bridge(p: ACSBridgeRequest):
    session = get_session(p.session_id)
    directive = {
        "filled": "USER_INPUT_RECEIVED", "noinput": "REQUEST_REPROMPT",
        "nomatch": "REQUEST_CLARIFICATION", "disconnect": "END_SESSION",
    }.get(p.vxml_event, "UNKNOWN")
    log(session, "acs_bridge", {"event": p.vxml_event, "directive": directive})
    bridge_payload = {
        "platform": "ACS", "directive": directive,
        "acs_call_connection_id": p.acs_call_connection_id,
        "tts_text": p.tts_text, "voice": "en-IN-NeerjaNeural",
        "collect_digits": p.collect_digits, "max_digits": p.max_digits,
        "language": session["language"], "context": session.get("booking_slots", {}),
    }
    return ok(f"VXML '{p.vxml_event}' → ACS '{directive}'", {
        "bridge_payload": bridge_payload,
        "m3_todo": f"Replace stub: conn.start_recognizing_media(...) with bridge_payload above",
    }, directive)

@app.get("/session/{session_id}", summary="Get Session State")
def get_session_info(session_id: str):
    return ok("Session retrieved.", get_session(session_id), "session_info")

@app.get("/health", summary="Health Check")
def health():
    return ok("IRCTC Smart IVR is running.", {
        "version": "2.0.0", "milestone": "M2",
        "active_sessions": len(SESSIONS),
        "endpoints": ["/ivr/start", "/ivr/input", "/ivr/pnr", "/ivr/booking", "/ivr/tatkal", "/ivr/tracking"],
    })

def _sub_prompt(digit):
    prompts = {
        "1": "Please enter your 10-digit PNR number followed by hash.",
        "2": "Select class: 1 Sleeper, 2 Third AC, 3 Second AC, 4 First AC, 5 Chair Car.",
        "3": "Tatkal booking. Enter your 5-digit train number followed by hash.",
        "4": "Live tracking. Enter your 5-digit train number followed by hash.",
        "5": "Cancellation. Enter your 10-digit PNR number followed by hash.",
    }
    return prompts.get(digit, "Please follow the instructions.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend:app", host="0.0.0.0", port=8000, reload=True)
