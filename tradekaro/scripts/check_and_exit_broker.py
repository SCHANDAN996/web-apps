import sys
import os

# Add src to python path
sys.path.append(os.path.abspath('src'))

from connector import ShoonyaConnector

def check_positions():
    print("Connecting to Shoonya Broker...")
    api = ShoonyaConnector()
    if api.login():
        print("Connected successfully! Fetching open positions...")
        positions = api.get_positions()
        if positions:
            print("\n--- Live Open Positions on Broker ---")
            for pos in positions:
                # In Shoonya, positions with netqty != '0' are open
                netqty = int(pos.get('netqty', 0))
                if netqty != 0:
                    print(f"Symbol: {pos.get('tsymbol')} | Net Qty: {netqty} | Buy Avg: {pos.get('buyavgprc')} | Sell Avg: {pos.get('sellavgprc')}")
        else:
            print("No open positions found on the broker account.")
    else:
        print("Failed to login to the broker API.")

if __name__ == "__main__":
    check_positions()
