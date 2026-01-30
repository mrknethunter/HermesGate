import requests
import socket
import json
import time
import os

CATCHMAIL_BASE_URL = "https://api.catchmail.io/api/v1"
EMAIL_ADDRESS = "mirko@catchmail.io"
LOGSTASH_HOST = "host.docker.internal"
LOGSTASH_PORT = 5000

POLL_INTERVAL = 10 
SEEN_FILE = "/tmp/seen_ids.txt"

def load_seen_ids():
    if not os.path.exists(SEEN_FILE):
        return set()
    with open(SEEN_FILE, "r") as f:
        return set(line.strip() for line in f if line.strip())

def save_seen_ids(ids):
    with open(SEEN_FILE, "w") as f:
        for i in ids:
            f.write(f"{i}\n")

def list_messages():
    try:
        r = requests.get(f"{CATCHMAIL_BASE_URL}/mailbox", params={"address": EMAIL_ADDRESS}, timeout=10)
        r.raise_for_status()
        return r.json().get("messages", [])
    except Exception as e:
        print("[ERR API list_messages]:", e)
        return []

def fetch_message_detail(msg_id):
    try:
        r = requests.get(f"{CATCHMAIL_BASE_URL}/message/{msg_id}", params={"mailbox": EMAIL_ADDRESS}, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"[ERR API fetch_message {msg_id}]:", e)
        return None

def normalize(msg):
    return {
        "sender": msg.get("from"),
        "receiver": EMAIL_ADDRESS,
        "date": msg.get("date"),
        "subject": msg.get("subject"),
        "body": msg.get("body", {}).get("text") or ""
    }

def send_to_logstash(json_msg):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((LOGSTASH_HOST, LOGSTASH_PORT))
            sock.sendall((json.dumps(json_msg) + "\n").encode("utf-8"))
    except Exception as e:
        print("[ERR TCP send]:", e)
        print(LOGSTASH_HOST, LOGSTASH_PORT)

def main():
    seen = load_seen_ids()
    print(f"{len(seen)} emails already processed")

    while True:
        msgs = list_messages()
        new_ids = []

        for m in msgs:
            mid = m.get("id")
            if not mid:
                continue
            if mid in seen:
                continue

            detail = fetch_message_detail(mid)
            if not detail:
                continue

            normalized = normalize(detail)
            send_to_logstash(normalized)

            seen.add(mid)
            new_ids.append(mid)

        if new_ids:
            print(f"Sent {len(new_ids)} NEW emails:", new_ids)
            save_seen_ids(seen)

        time.sleep(POLL_INTERVAL) # evitiamo il ban

if __name__ == "__main__":
    main()
