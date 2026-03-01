from fastapi import FastAPI
from fastapi.responses import Response
from models import CallInput
from session_manager import start_session, get_session, end_session
from ai_engine import detect_intent
from bap_services import get_pnr_status, cancel_ticket
from vxml_response import vxml_say, vxml_gather

app = FastAPI(title="IVR Middleware Integration API")

# 1️⃣ Start Call
@app.post("/call/start")
def start_call(call_id: str):
    start_session(call_id)
    msg = "Welcome to IRCTC. Press 1 for PNR status. Press 2 to cancel ticket."
    return Response(vxml_gather(msg), media_type="application/xml")


# 2️⃣ Receive Input
@app.post("/call/input")
def process_input(data: CallInput):

    intent = detect_intent(data.input)

    if intent == "PNR_STATUS":
        msg = "Please enter your 10 digit PNR number"
        return Response(vxml_gather(msg), media_type="application/xml")

    elif intent == "CANCEL_TICKET":
        result = cancel_ticket()
        end_session(data.call_id)
        return Response(vxml_say(result), media_type="application/xml")

    elif intent == "AGENT":
        end_session(data.call_id)
        return Response(vxml_say("Connecting to customer care agent"), media_type="application/xml")

    return Response(vxml_say("Invalid option"), media_type="application/xml")


# 3️⃣ Fetch PNR
@app.post("/call/pnr/{pnr}")
def pnr_lookup(call_id: str, pnr: str):
    result = get_pnr_status(pnr)
    end_session(call_id)
    return Response(vxml_say(result), media_type="application/xml")


# 4️⃣ End Call
@app.post("/call/end")
def end_call(call_id: str):
    end_session(call_id)
    return {"status": "call ended"}