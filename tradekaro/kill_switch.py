"""Emergency stop for TradeKaro.

Stops the bot, closes every open position, and deliberately leaves the bot
down so a human decides when trading resumes.

Triggered by sending "KILL ALL" to the Telegram listener, or by running this
file directly:  venv/bin/python kill_switch.py
"""
import logging
import os

import requests
from dotenv import load_dotenv

load_dotenv('config/credentials.env')


def _notify(text):
    """Best-effort Telegram alert. A failed alert must never break the stop."""
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    if not token or not chat_id:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={'chat_id': chat_id, 'text': text},
            timeout=10,
        )
    except Exception as e:
        logging.error(f"[KILL SWITCH] Could not send Telegram alert: {e}")


def emergency_kill_switch():
    """Stop trading now and close all open positions.

    The bot is NOT restarted afterwards — bring it back with
    `systemctl start tradekaro-bot` once the situation is understood.
    Returns the number of positions closed.
    """
    logging.critical("[KILL SWITCH] Emergency stop triggered.")
    print("🔴 EMERGENCY KILL SWITCH ACTIVATED")

    try:
        # Imported here so merely importing this module stays cheap and free of
        # side effects — force_exit_all pulls in the broker connector.
        from force_exit_all import exit_all
        closed = exit_all(restart_bot=False)
    except Exception as e:
        logging.critical(f"[KILL SWITCH] Failed while closing positions: {e}")
        _notify(
            f"🔴 KILL SWITCH FAILED: {e}\n"
            "The bot has been stopped, but positions may still be open. "
            "Check the broker terminal manually."
        )
        raise

    msg = (
        "🔴 EMERGENCY STOP COMPLETE\n"
        f"Closed {closed} open position(s).\n"
        "The bot is stopped and will NOT restart on its own.\n"
        "To resume: systemctl start tradekaro-bot"
    )
    print(msg)
    _notify(msg)
    return closed


if __name__ == "__main__":
    emergency_kill_switch()
