import requests, json, hashlib, datetime

# === CONFIG ===
XO_HOST = "XOA_URL"
TOKEN = "XOA_API_KEY"
HEADERS = {"Cookie": f"authenticationToken={TOKEN}"}

# === 1. Fetch backup log paths
print("[1/3] Fetching backup log paths...")
log_paths = requests.get(f"{XO_HOST}/rest/v0/backup/logs", headers=HEADERS).json()

# === 2. Create log summaries
print("[2/3] Creating log summaries...")
log_summaries = []
for path in log_paths[:2]:  # Limited [:2] for testing
    log_id = path.split("/")[-1]
    r = requests.get(XO_HOST + path, headers=HEADERS)
    log = r.json()
    summary = {
        "id": log_id,
        "job": log.get("jobName") or log.get("jobId"),
        "vm": log.get("vm") or "unknown",
        "status": log.get("status"),
        "start": log.get("start"),
        "end": log.get("end"),
    }
    log_summaries.append(summary)

# === 3. Hash and output JSON
today = datetime.date.today().isoformat()
snapshot_json = json.dumps(log_summaries, sort_keys=True)
snapshot_hash = hashlib.sha256(snapshot_json.encode()).hexdigest()

anchor_metadata = {
    "date": today,
    "snapshot_hash": snapshot_hash,
    "timestamp": str(datetime.datetime.utcnow())
}

with open("daily_log_anchor.json", "w") as f:
    json.dump(anchor_metadata, f, indent=2)

print(f"[3/3] Saved anchor: daily_log_anchor.json\nSnapshot hash: {snapshot_hash}")
