from flask import Flask, request
from flask_restful import Api, Resource
import yfinance as yf
import pandas as pd

# -------------------------------
# CONFIG
# -------------------------------
OBV_LOOKBACK = 20
RSI_PERIOD = 14

# -------------------------------
# TECHNICAL ANALYZER CLASS
# -------------------------------
class TechnicalAnalyzer:
    """Fetches stock data, calculates RSI & OBV, returns simple signal."""

    def __init__(self, ticker):
        self.ticker = ticker.upper()
        self.data = None

    def fetch_data(self):
        df = yf.download(self.ticker, period="1y", progress=False, auto_adjust=False)
        if df.empty:
            raise ValueError(f"Could not fetch data for ticker: {self.ticker}")

        # Flatten multi-index columns if present
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Keep only necessary columns
        if 'Close' not in df.columns or 'Volume' not in df.columns:
            raise ValueError(f"'Close' or 'Volume' column missing for {self.ticker}")

        self.data = df[['Close', 'Volume']].dropna()

    def calculate_rsi(self):
        delta = self.data['Close'].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.rolling(RSI_PERIOD).mean()
        avg_loss = loss.rolling(RSI_PERIOD).mean()
        rs = avg_gain / avg_loss
        self.data['RSI'] = 100 - (100 / (1 + rs))

    def calculate_obv_change(self):
        obv = [0]
        for i in range(1, len(self.data)):
            if self.data['Close'].iloc[i] > self.data['Close'].iloc[i-1]:
                obv.append(obv[-1] + self.data['Volume'].iloc[i])
            elif self.data['Close'].iloc[i] < self.data['Close'].iloc[i-1]:
                obv.append(obv[-1] - self.data['Volume'].iloc[i])
            else:
                obv.append(obv[-1])
        self.data['OBV'] = obv
        return self.data['OBV'].iloc[-1] - self.data['OBV'].iloc[-OBV_LOOKBACK]

    def generate_signal(self):
        current_rsi = self.data['RSI'].iloc[-1]
        obv_change = self.calculate_obv_change()

        # Determine Bullish/Bearish/Neutral
        if (current_rsi <= 30 and obv_change > 0) or obv_change > 0:
            signal = "Bullish"
            action = "Buy or Hold"
        elif (current_rsi >= 70 and obv_change < 0) or obv_change < 0:
            signal = "Bearish"
            action = "Sell or Avoid Buying"
        else:
            signal = "Neutral"
            action = "Hold / Wait"

        commentary = f"RSI: {current_rsi:.2f} "
        commentary += f"({'Oversold' if current_rsi<=30 else 'Overbought' if current_rsi>=70 else 'Neutral'}). "
        commentary += f"OBV trend (20 days): {'upwards' if obv_change>0 else 'downwards' if obv_change<0 else 'flat'}."

        return {
            "ticker": self.ticker,
            "current_price": float(self.data['Close'].iloc[-1]),
            "signal": signal,
            "suggested_action": action,
            "commentary": commentary
        }

# -------------------------------
# FLASK RESOURCE
# -------------------------------
class TechnicalSignal(Resource):
    def get(self):
        stock_ticker = request.args.get("stock", "").upper()
        if not stock_ticker:
            return {"error": "Stock ticker is required"}, 400

        try:
            analyzer = TechnicalAnalyzer(stock_ticker)
            analyzer.fetch_data()
            analyzer.calculate_rsi()
            result = analyzer.generate_signal()
            return result, 200
        except Exception as e:
            import traceback
            print("❌ Error:", e)
            traceback.print_exc()
            return {"error": f"Failed to generate signal: {str(e)}"}, 500

