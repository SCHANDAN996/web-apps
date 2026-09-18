import time
import requests
import os
import logging
from dotenv import load_dotenv
from kill_switch import emergency_kill_switch
from src.database import TradingDB
from src.brain import TradingBrain
from src.chat_agent import ChatAgent

load_dotenv('config/credentials.env')

TOKEN = os.getenv('TELEGRAM_TOKEN')
# Using Chat ID as the Authorized User ID filter. 
# Make sure your config/credentials.env TELEGRAM_CHAT_ID matches your user ID.
AUTHORIZED_USER_ID = os.getenv('TELEGRAM_CHAT_ID')

def get_updates(offset=None):
    if not TOKEN: return {}
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    params = {'timeout': 100, 'offset': offset}
    try:
        response = requests.get(url, params=params)
        return response.json()
    except Exception as e:
        print(f"⚠️ Telegram Polling Error: {e}")
        return {}

def send_telegram_msg(chat_id, text):
    if not TOKEN: return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {'chat_id': chat_id, 'text': text}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"⚠️ Telegram Send Error: {e}")

def listen():
    if not TOKEN or not AUTHORIZED_USER_ID:
        print("❌ Credentials missing. Cannot start listener.")
        return

    print(f"🎧 Telegram Listener Active. Listening for 'KILL ALL' from ID: {AUTHORIZED_USER_ID}")
    
    offset = None
    while True:
        try:
            updates = get_updates(offset)
            if "result" in updates and updates["result"]:
                for u in updates["result"]:
                    offset = u["update_id"] + 1
                    
                    message = u.get('message', {})
                    if not message: continue
                    
                    user_id = str(message.get('from', {}).get('id'))
                    text = message.get('text', '').upper().strip()
                    
                    if user_id == str(AUTHORIZED_USER_ID):
                        if text == "KILL ALL":
                            print(f"🔴 RECEIVED KILL SIGNAL FROM {user_id}")
                            send_telegram_msg(user_id, "🔴 Emergency stop starting — closing all open positions...")
                            try:
                                # Reports the outcome over Telegram itself.
                                emergency_kill_switch()
                            except Exception as e:
                                print(f"❌ Kill switch failed: {e}")
                        elif text == "PING":
                            print("Received PING")
                        else:
                            # Send normal messages to the Smart Chat Agent
                            from src.database import TradingDB
                            from src.brain import TradingBrain
                            from src.chat_agent import ChatAgent
                            
                            db = TradingDB('trading_data.db')
                            brain = TradingBrain()
                            agent = ChatAgent(db, brain)
                            
                            reply_text = agent.process_message(text)
                            
                            send_telegram_msg(str(AUTHORIZED_USER_ID), reply_text)
                    else:
                        print(f"⚠️ Unauthorized command '{text}' from {user_id}")
            
            time.sleep(2)
        except KeyboardInterrupt:
            print("🛑 Listener Stopped.")
            break
        except Exception as e:
            print(f"⚠️ Listen Loop Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    listen()
