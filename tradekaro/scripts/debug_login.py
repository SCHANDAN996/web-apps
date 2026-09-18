from src.connector import ShoonyaConnector
import logging

# Configure logging to stdout
logging.basicConfig(level=logging.DEBUG)

print("Attempting Login...")
bot = ShoonyaConnector()
if bot.login():
    print("Login SUCCESS!")
    print(f"Session Token: {bot.susertoken}")
else:
    print("Login FAILED!")
