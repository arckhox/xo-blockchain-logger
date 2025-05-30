import requests
import json

# === CONFIGURATION ===
BOT_TOKEN = "YOUR_TELEGRAM_BOT_API"
GROUP_ID = "TELEGRAM_GROUP_ID"
NANO_RPC = "https://rpc.nano.to"
NANO_API_KEY = "NANO_API_KEY"

def send_telegram(message, success=True):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": GROUP_ID,
        "text": message,
        "parse_mode": "Markdown" if not success else None
    }
    requests.post(url, data=data)

# === Load the local anchor metadata (log hash) ===
try:
    with open("daily_log_anchor.json") as f:
        anchor = json.load(f)
    snapshot_hash = anchor["snapshot_hash"]
    snapshot_date = anchor.get("date", "")
except Exception as e:
    send_telegram(f"❌ *Fout*: daily_log_anchor.json niet gevonden of onleesbaar!\n{str(e)}", success=False)
    exit(1)

# === Load the Nano proof metadata (TX hash) ===
try:
    with open("nano_tx_proof.json") as f:
        proof = json.load(f)
    tx_hash = proof["nano_tx_hash"]
except Exception as e:
    send_telegram(f"❌ *Fout*: nano_tx_proof.json niet gevonden of onleesbaar!\n{str(e)}", success=False)
    exit(1)

# === Fetch block info from Nano ===
try:
    resp = requests.post(
        NANO_RPC,
        json={
            "action": "block_info",
            "json_block": "true",
            "hash": tx_hash
        },
        headers={"Authorization": f"Bearer {NANO_API_KEY}"}
    )
    info = resp.json()
    if "contents" not in info:
        raise Exception(f"block_info error: {info}")
    onchain_link = info["contents"]["link"].lower()
except Exception as e:
    send_telegram(f"❌ *Fout bij ophalen van blockchain data*: {str(e)}", success=False)
    exit(1)

# === Verification Logic ===
if onchain_link == snapshot_hash.lower():
    send_telegram(
        f"✅ Log geverifieerd voor {snapshot_date}!\n*Hash* komt overeen op de Nano blockchain.\nTX: `{tx_hash}`"
    )
else:
    send_telegram(
        f"⚠️ *MISMATCH!*\n*Log hash*: `{snapshot_hash}`\n*On-chain*: `{onchain_link}`\n*TX*: `{tx_hash}`\n\nControleer op mogelijke manipulatie!",
        success=False
    )
