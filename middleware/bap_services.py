def get_pnr_status(pnr):
    if pnr == "1234567890":
        return "Your ticket is confirmed in coach S5 seat 32"
    return "PNR not found"

def cancel_ticket():
    return "Your ticket has been cancelled successfully"