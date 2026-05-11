import urllib.request, json
url = 'http://localhost:8000/ivr/start'
req = urllib.request.Request(url, data=json.dumps({'caller_id': '+919876543210', 'language': 'EN'}).encode('utf-8'), headers={'Content-Type': 'application/json'})
with urllib.request.urlopen(req) as r:
    result = json.loads(r.read().decode())
    print(json.dumps(result, indent=2))
