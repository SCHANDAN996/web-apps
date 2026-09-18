from src.database import TradingDB

print("Starting Database Cleanup...")
db = TradingDB()
rows = db.clean_redundant_data()
print(f"Cleanup Complete. {rows} rows deleted.")