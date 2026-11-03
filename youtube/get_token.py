"""One-time: PC par chalayein, browser me login karein, refresh token print hoga.

Usage: python youtube/get_token.py path/to/client_secret.json
Client me redirect URI http://localhost:8080/ add hona chahiye.
"""
import json
import sys

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

path = sys.argv[1]
with open(path, encoding="utf-8") as f:
    raw = json.load(f)
cfg = raw.get("installed") or raw["web"]

flow = InstalledAppFlow.from_client_config({"installed": cfg}, SCOPES)
creds = flow.run_local_server(port=8080, access_type="offline", prompt="consent")

print("\nGitHub Secrets me ye teen value daalein:\n")
print("YT_CLIENT_ID     =", cfg["client_id"])
print("YT_CLIENT_SECRET = (client_secret JSON se)")
print("YT_REFRESH_TOKEN =", creds.refresh_token)
