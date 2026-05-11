import urllib.request, json

def api_call(endpoint, payload):
    url = f'http://localhost:8000{endpoint}'
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode())

# Start session
start_resp = api_call('/ivr/start', {'caller_id': '+919876543210', 'language': 'EN'})
session_id = start_resp['data']['session_id']
print("1. START RESPONSE:")
print(f"   {start_resp['prompt']}\n")

# Book ticket (option 1)
book_resp = api_call('/ivr/input', {'session_id': session_id, 'digit': '1', 'current_flow': 'main_menu'})
print("2. BOOKING FLOW:")
print(f"   {book_resp['prompt']}\n")

# Select class (option 2 = Third AC)
class_resp = api_call('/ivr/input', {'session_id': session_id, 'digit': '2', 'current_flow': 'select_class'})
print("3. CLASS SELECTED:")
print(f"   {class_resp['prompt']}\n")

# Select quota (option 1 = General)
quota_resp = api_call('/ivr/input', {'session_id': session_id, 'digit': '1', 'current_flow': 'select_quota'})
print("4. QUOTA SELECTED:")
print(f"   {quota_resp['prompt']}\n")

# Select berth (option 1 = Lower)
berth_resp = api_call('/ivr/input', {'session_id': session_id, 'digit': '1', 'current_flow': 'select_berth'})
print("5. BERTH SELECTED:")
print(f"   {berth_resp['prompt']}\n")

# PNR Check
pnr_resp = api_call('/ivr/pnr', {'session_id': session_id, 'pnr_number': '1234567890'})
print("6. PNR STATUS:")
print(f"   {pnr_resp['prompt']}\n")

# Train Tracking
track_resp = api_call('/ivr/tracking', {'session_id': session_id, 'train_number': '12951'})
print("7. TRAIN TRACKING:")
print(f"   {track_resp['prompt']}\n")
