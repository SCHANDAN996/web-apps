import requests
import os
from dotenv import load_dotenv

load_dotenv('config/credentials.env')

class TelegramNotifier:
    def __init__(self):
        self.token = os.getenv('TELEGRAM_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')

    def send_message(self, text):
        """Telegram पर मैसेज भेजने के लिए"""
        if not self.token or not self.chat_id or 'REPLACE_WITH' in self.token:
            print("[WARN] Telegram Notification Skipped (Placeholder Credentials)")
            return
            
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML"
        }
        
        try:
            response = requests.post(url, data=payload, timeout=5)
            return response.json()
        except Exception as e:
            print(f"❌ Telegram Error: {e}")
