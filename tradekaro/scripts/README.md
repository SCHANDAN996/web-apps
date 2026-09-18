# Utility Scripts & Diagnostics

This directory contains standalone maintenance, diagnostic, and manual utility scripts for TradeKaro AI. These scripts are isolated from the main live trading engine.

- `debug_*.py`: Database inspection and Shoonya login connection diagnostics.
- `test_*.py`: Standalone integration/feature tests (for unit tests, see `tests/`).
- `cleanup_*.py`: Database pruning, maintenance, and table recreation scripts.
- `check_*.py`: Broker position and database table status utilities.
- `fetch_yfinance_history.py`: Manual historical dataset downloader.
