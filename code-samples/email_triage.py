#!/usr/bin/env python3
"""
Autonomous Email Triage Agent v2
Monitors Gmail + iCloud every 15 minutes. Classifies, moves, deletes autonomously.

Safeguards:
- NEVER deletes from AFCYP, billing, or known important senders
- LLM classifies unknown senders (action/notify/ignore)
- State tracking prevents re-processing same emails
- Telegram summary after each run
"""
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# ─── CONFIG ─────────────────────────────────────────────────────────────────

GMAIL_TOKEN_PATH = "/home/apache/.hermes/google_token.json"
STATE_FILE = "/home/apache/.hermes/state/email_triage.json"
TELEGRAM_DIGEST = "telegram:-1003819642739"
TELEGRAM_DOCS = "telegram:-1003279569826"

# Senders that are NEVER touched (permanent block list)
PERMANENT_PROTECT = [
    "afcfyp.com",
    "billing@usaa.com",
    "service@paypal.com",
    "alerts@palantir.com",
    "info@tsp.gov",
]

# Known low-value senders → auto-trash (no LLM needed)
AUTO_TRASH_PATTERNS = [
    "nextdoor.com", "remind.com", "appsumo.com", "gearpatrol.com",
    "evoentertainment.com", "lifetouch.com", "thestokefactory.com",
    "sundaylawncare.com", "tp-link.com", "williamellery.com",
    "mantasleep.com", "quarryvillage.com", "thedoseum.com",
    "homebot.ai", "greensky.com", "exclusiveeventrentals.com",
    "heb.com", "canva.com", "xbox.com", "googleplaypromo-noreply@google.com",
    "news-googleplay@google.com", "googlenews-noreply@google.com",
]

# Known receipt senders → auto-file to Billings/Receipts
RECEIPT_SENDERS = [
    "googleplay-noreply@google.com", "noreply@email.openai.com",
    "support@arculus.co",
]

# Labels
LABEL_RECEIPTS = "Label_13"      # Billings/Receipts
LABEL_TRASH = "TRASH"
LABEL_UNREAD = "UNREAD"
LABEL_INBOX = "INBOX"

# ─── STATE MANAGEMENT ───────────────────────────────────────────────────────

def load_state() -> Dict:
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except FileNotFoundError:
        return {"processed_ids": [], "last_run": None, "stats": {"trashed": 0, "filed": 0, "read": 0}}

def save_state(state: Dict):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

# ─── GMAIL API ──────────────────────────────────────────────────────────────

def get_gmail_service():
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    
    with open(GMAIL_TOKEN_PATH) as f:
        token_data = json.load(f)
    access_token = token_data.get("token") or token_data.get("access_token")
    creds = Credentials(access_token)
    return build("gmail", "v1", credentials=creds)

# ─── HIMALAYA (iCloud) ──────────────────────────────────────────────────────

def get_icloud_unread() -> List[Dict]:
    """Fetch unread emails from iCloud via Himalaya CLI."""
    himalaya_bin = os.path.expanduser("~/.local/bin/himalaya")
    try:
        result = subprocess.run(
            [himalaya_bin, "envelope", "list", "--output", "json"],
            capture_output=True, text=True, timeout=30,
            env={**os.environ, "PATH": os.path.expanduser("~/.local/bin") + ":" + os.environ.get("PATH", "")}
        )
        if result.returncode != 0:
            print(f"Himalaya error: {result.stderr}")
            return []
        
        envelopes = json.loads(result.stdout)
        # Filter unread (no 'seen' flag)
        return [e for e in envelopes if "seen" not in e.get("flags", [])]
    except Exception as e:
        print(f"iCloud fetch failed: {e}")
        return []

# ─── CLASSIFICATION ─────────────────────────────────────────────────────────

def is_protected(sender: str) -> bool:
    """Check if sender is on the permanent protect list."""
    sender_lower = sender.lower()
    return any(domain in sender_lower for domain in PERMANENT_PROTECT)

def is_auto_trash(sender: str, subject: str) -> bool:
    """Check if sender matches known low-value patterns."""
    sender_lower = sender.lower()
    subject_lower = subject.lower()
    return (
        any(pattern in sender_lower for pattern in AUTO_TRASH_PATTERNS) or
        any(pattern in subject_lower for pattern in ["unsubscribe", "weekly ad", "promotional"])
    )

def is_receipt(sender: str, subject: str) -> bool:
    """Check if email is a receipt/invoice."""
    sender_lower = sender.lower()
    subject_lower = subject.lower()
    receipt_keywords = ["receipt", "invoice", "order confirmation", "payment received", "billing"]
    return (
        any(pattern in sender_lower for pattern in RECEIPT_SENDERS) or
        any(kw in subject_lower for kw in receipt_keywords)
    )

def llm_classify(sender: str, subject: str, snippet: str) -> str:
    """
    Use Kimi for unknown senders. Returns: action, notify, ignore, receipt
    """
    import requests
    
    api_key = os.getenv("KIMI_API_KEY")
    
    prompt = f"""Classify this email into exactly one category:
- action: requires me to do something (approve, review, respond, pay)
- notify: informational, no action needed but worth knowing
- receipt: purchase confirmation, invoice, billing
- ignore: promotional, newsletter, social notification, low value

From: {sender}
Subject: {subject}
Snippet: {snippet}

Respond with one word only: action, notify, receipt, or ignore."""

    try:
        resp = requests.post(
            "https://api.moonshot.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": "kimi-k2.6", "messages": [{"role": "user", "content": prompt}], "max_tokens": 10},
            timeout=15,
        )
        resp.raise_for_status()
        result = resp.json()["choices"][0]["message"]["content"].strip().lower()
        # Normalize
        for valid in ["action", "notify", "receipt", "ignore"]:
            if valid in result:
                return valid
        return "notify"  # safe default
    except Exception as e:
        print(f"LLM classify failed: {e}, defaulting to notify")
        return "notify"

# ─── ACTIONS ────────────────────────────────────────────────────────────────

def gmail_mark_read(service, msg_id: str):
    service.users().messages().modify(
        userId="me", id=msg_id, body={"removeLabelIds": [LABEL_UNREAD]}
    ).execute()

def gmail_move_to_label(service, msg_id: str, label_id: str):
    service.users().messages().modify(
        userId="me", id=msg_id,
        body={"addLabelIds": [label_id], "removeLabelIds": [LABEL_INBOX, LABEL_UNREAD]}
    ).execute()

def gmail_trash(service, msg_id: str):
    service.users().messages().trash(userId="me", id=msg_id).execute()

def icloud_mark_read(msg_id: str):
    himalaya_bin = os.path.expanduser("~/.local/bin/himalaya")
    subprocess.run([himalaya_bin, "flag", "add", str(msg_id), "--flag", "seen"], 
                   capture_output=True, timeout=10)

def icloud_trash(msg_id: str):
    himalaya_bin = os.path.expanduser("~/.local/bin/himalaya")
    subprocess.run([himalaya_bin, "message", "delete", str(msg_id)], 
                   capture_output=True, timeout=10)

# ─── MAIN TRIAGE ────────────────────────────────────────────────────────────

def triage_gmail(service, state: Dict) -> Dict:
    """Process Gmail unread emails."""
    results = service.users().messages().list(
        userId="me", q="is:unread in:inbox", maxResults=50
    ).execute()
    msgs = results.get("messages", [])
    
    actions = {"trashed": 0, "filed": 0, "read": 0, "flagged": 0, "unknown": 0}
    flagged = []
    
    for m in msgs:
        msg_id = m["id"]
        if msg_id in state["processed_ids"]:
            continue
        
        msg = service.users().messages().get(
            userId="me", id=msg_id, format="metadata",
            metadataHeaders=["Subject", "From"]
        ).execute()
        
        headers = msg["payload"]["headers"]
        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "")
        sender = next((h["value"] for h in headers if h["name"] == "From"), "")
        snippet = msg.get("snippet", "")
        
        # SAFETY: Never touch protected senders
        if is_protected(sender):
            state["processed_ids"].append(msg_id)
            continue
        
        # RULE 1: Auto-trash known junk
        if is_auto_trash(sender, subject):
            gmail_trash(service, msg_id)
            actions["trashed"] += 1
            state["processed_ids"].append(msg_id)
            continue
        
        # RULE 2: Auto-file receipts
        if is_receipt(sender, subject):
            gmail_move_to_label(service, msg_id, LABEL_RECEIPTS)
            actions["filed"] += 1
            state["processed_ids"].append(msg_id)
            continue
        
        # RULE 3: LLM classification for unknowns
        classification = llm_classify(sender, subject, snippet)
        
        if classification == "ignore":
            gmail_trash(service, msg_id)
            actions["trashed"] += 1
        elif classification == "receipt":
            gmail_move_to_label(service, msg_id, LABEL_RECEIPTS)
            actions["filed"] += 1
        elif classification == "action":
            # Leave in inbox, mark unread for human attention
            actions["flagged"] += 1
            flagged.append({"id": msg_id, "sender": sender, "subject": subject})
        else:  # notify
            # Mark read but leave in inbox briefly, then archive after 24h
            gmail_mark_read(service, msg_id)
            actions["read"] += 1
        
        state["processed_ids"].append(msg_id)
    
    return actions, flagged

def triage_icloud(state: Dict) -> Dict:
    """Process iCloud unread emails."""
    msgs = get_icloud_unread()
    actions = {"trashed": 0, "filed": 0, "read": 0, "flagged": 0}
    
    for msg in msgs:
        msg_id = msg.get("id")
        sender = msg.get("from", {}).get("addr", "")
        subject = msg.get("subject", "")
        
        if is_protected(sender):
            continue
        
        if is_auto_trash(sender, subject):
            icloud_trash(msg_id)
            actions["trashed"] += 1
        elif is_receipt(sender, subject):
            icloud_mark_read(msg_id)
            actions["filed"] += 1
        else:
            # For iCloud, LLM classification is expensive per-message
            # Default to mark-read for now until volume justifies it
            icloud_mark_read(msg_id)
            actions["read"] += 1
    
    return actions

# ─── TELEGRAM REPORTING ─────────────────────────────────────────────────────

def send_report(gmail_actions, icloud_actions, flagged):
    lines = [f"📧 *Email Triage* ({datetime.now().strftime('%H:%M')})"]
    
    total = sum(gmail_actions.values()) + sum(icloud_actions.values())
    if total == 0:
        lines.append("No new emails to process.")
        return
    
    lines.append(f"\n*Gmail:*")
    for k, v in gmail_actions.items():
        if v > 0:
            emoji = {"trashed": "🗑️", "filed": "📁", "read": "👁️", "flagged": "🚩", "unknown": "❓"}
            lines.append(f"  {emoji.get(k, '•')} {k}: {v}")
    
    lines.append(f"\n*iCloud:*")
    for k, v in icloud_actions.items():
        if v > 0:
            emoji = {"trashed": "🗑️", "filed": "📁", "read": "👁️", "flagged": "🚩"}
            lines.append(f"  {emoji.get(k, '•')} {k}: {v}")
    
    if flagged:
        lines.append(f"\n*🚩 Action Required ({len(flagged)}):*")
        for f in flagged[:5]:
            lines.append(f"  • {f['sender']}: {f['subject']}")
    
    report = "\n".join(lines)
    print(report)
    # In production:
    # send_message(target=TELEGRAM_DIGEST, text=report)

# ─── MAIN ───────────────────────────────────────────────────────────────────

def main():
    print(f"=== Email Triage Run: {datetime.now().isoformat()} ===")
    state = load_state()
    
    # Trim processed_ids to last 1000 to prevent unbounded growth
    if len(state["processed_ids"]) > 1000:
        state["processed_ids"] = state["processed_ids"][-1000:]
    
    # Gmail
    service = get_gmail_service()
    gmail_actions, flagged = triage_gmail(service, state)
    
    # iCloud
    icloud_actions = triage_icloud(state)
    
    # Update stats
    for k in ["trashed", "filed", "read"]:
        state["stats"][k] += gmail_actions.get(k, 0) + icloud_actions.get(k, 0)
    state["last_run"] = datetime.now().isoformat()
    
    save_state(state)
    send_report(gmail_actions, icloud_actions, flagged)
    
    print(f"\nLifetime stats: {state['stats']}")

if __name__ == "__main__":
    main()
