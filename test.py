# pip install yfinance

import yfinance as yf

def get_stock_data(ticker):
    ticker = ticker.upper() + ".NS"  # Append .NS for NSE
    stock = yf.Ticker(ticker)
    info = stock.info
    
    print(f"----- All Data for {ticker} -----")
    for key, value in info.items():
        print(f"{key}: {value}")


symbol = input("Enter NSE ticker (e.g. INFY, TCS, RELIANCE): ")
get_stock_data(symbol)
