import yfinance as yf
tickers = ["SBIN.NS", "KOTAKBANK.NS", "INFY.NS", "LT.NS"]
for t in tickers:
    data = yf.download(t, period="1d", interval="1m", progress=False)
    if not data.empty:
        print(f"{t}: {data['Close'].iloc[-1]}")
    else:
        print(f"{t}: No Data")
