def detect_intent(text):
    text = text.lower()

    if "1" in text or "pnr" in text:
        return "PNR_STATUS"
    elif "2" in text or "cancel" in text:
        return "CANCEL_TICKET"
    elif "agent" in text:
        return "AGENT"
    else:
        return "UNKNOWN"