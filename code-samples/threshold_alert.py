#!/usr/bin/env python3
"""
Threshold Alert Agent
Alerts only when a value crosses a configured threshold.
Prevents notification fatigue by tracking state transitions.

Usage:
    check_thresholds()  # Run on schedule (every 2 hours)
"""
import json
import os
from datetime import datetime

# Alert configurations
ALERTS = [
    {"ticker": "XRP", "type": "above", "threshold": 2.50, "message": "🚀 XRP broke $2.50!"},
    {"ticker": "ACHR", "type": "below", "threshold": 8.00, "message": "⚠️ ACHR dropped below $8"},
    {"ticker": "PLTR", "type": "above", "threshold": 100.0, "message": "📈 PLTR hit $100"},
]

STATE_FILE = "/home/apache/.hermes/state/alerts.json"


def load_alert_state() -> dict:
    """Load the last known prices from state file."""
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_alert_state(state: dict):
    """Persist current prices to state file."""
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


def get_price(ticker: str) -> float:
    """
    Fetch current price for a ticker.
    In production, this calls a price API or web scraper.
    """
    # Placeholder: replace with actual API call
    import random
    return random.uniform(1.0, 150.0)


def send_alert(message: str):
    """Send alert via Telegram."""
    print(f"ALERT: {message}")
    # In production:
    # send_message(target="telegram:-1003819642739", text=message)


def check_thresholds():
    """
    Check all configured thresholds and alert on state transitions.
    
    Design principle: Alert fatigue kills vigilance.
    We only notify when a threshold is CROSSED, not every poll.
    """
    state = load_alert_state()
    
    for alert in ALERTS:
        ticker = alert["ticker"]
        price = get_price(ticker)
        last_price = state.get(ticker, price)  # Default to current if no history
        
        crossed = False
        
        if alert["type"] == "above":
            # Was below, now above
            crossed = last_price < alert["threshold"] <= price
        elif alert["type"] == "below":
            # Was above, now below
            crossed = last_price > alert["threshold"] >= price
        
        if crossed:
            message = f"{alert['message']} (now ${price:.2f})"
            send_alert(message)
            print(f"[{datetime.now().isoformat()}] {ticker}: threshold crossed")
        else:
            print(f"[{datetime.now().isoformat()}] {ticker}: ${price:.2f} (no change)")
        
        # Always update state with current price
        state[ticker] = price
    
    save_alert_state(state)


if __name__ == "__main__":
    check_thresholds()
