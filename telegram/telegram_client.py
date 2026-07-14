"""Raw Telegram Bot HTTP API wrapper — no SDK dependency, same
stdlib-only style as scripts/ghl_api.py. No persistent bot process: the
orchestrator polls getUpdates once at the top of each scheduled run.
"""
import json
import urllib.error
import urllib.parse
import urllib.request

API_BASE = "https://api.telegram.org/bot{token}"


def get_updates(token, offset=None, timeout=0):
    params = {"timeout": timeout}
    if offset is not None:
        params["offset"] = offset
    url = f"{API_BASE.format(token=token)}/getUpdates?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=timeout + 10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def send_message(token, chat_id, text):
    url = f"{API_BASE.format(token=token)}/sendMessage"
    data = json.dumps({"chat_id": chat_id, "text": text}).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"ok": False, "error": e.read().decode("utf-8")}
