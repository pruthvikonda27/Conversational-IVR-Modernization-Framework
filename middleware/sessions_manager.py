sessions = {}

def start_session(call_id):
    sessions[call_id] = {"state": "START"}
    return sessions[call_id]

def get_session(call_id):
    return sessions.get(call_id)

def end_session(call_id):
    if call_id in sessions:
        del sessions[call_id]