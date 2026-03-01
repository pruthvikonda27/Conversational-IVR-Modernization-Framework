def detect_intent(user_input):
    text = user_input.lower()

    if text == "1" or "pnr" in text:
        return "PNR_STATUS"

    if text == "2" or "cancel" in text:
        return "CANCEL_TICKET"

    if text == "9":
        return "AGENT"

    return "UNKNOWN"