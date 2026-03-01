from fastapi import FastAPI
from fastapi.responses import Response
from models import IVRRequest
from ai_engine import detect_intent
from bap_services import get_pnr_status, cancel_ticket
from vxml_generator import vxml_response

app = FastAPI()

# Call Start
@app.post("/call/start")
def start_call():
    msg = "Welcome to IRCTC. Press 1 for PNR status. Press 2 to cancel ticket."
    return Response(vxml_response(msg, gather=True), media_type="application/xml")


# Handle Input from Legacy IVR
@app.post("/call/input")
def handle_input(req: IVRRequest):

    intent = detect_intent(req.input)

    if intent == "PNR_STATUS":
        msg = "Please enter your 10 digit PNR number"
        return Response(vxml_response(msg, gather=True), media_type="application/xml")

    elif intent == "CANCEL_TICKET":
        result = cancel_ticket()
        return Response(vxml_response(result), media_type="application/xml")

    else:
        return Response(vxml_response("Invalid option"), media_type="application/xml")


# Backend Transaction Example
@app.post("/call/pnr/{pnr}")
def pnr_lookup(pnr: str):
    result = get_pnr_status(pnr)
    return Response(vxml_response(result), media_type="application/xml")