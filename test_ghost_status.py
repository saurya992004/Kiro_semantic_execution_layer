import requests, json
r = requests.get('http://localhost:8000/api/ghost-mode/status', timeout=30)
data = r.json()
print("Active:", data.get("active"))
print("Last run:", data.get("last_run"))
a = data.get("latest_analysis", {})
errors = a.get("possible_errors_or_alerts", [])
print(f"Errors found: {len(errors)}")
for e in errors:
    print(f"  - text={str(e.get('text','?'))[:80]}, severity={e.get('severity','MISSING')}")
