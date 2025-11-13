from flask import Flask, request
from flask_restful import Api, Resource, reqparse
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from sklearn.preprocessing import MinMaxScaler

# -------------------------------
# CONFIG
# -------------------------------
LOOK_BACK = 60
FORECAST_DAYS = 14

app = Flask(__name__)
api = Api(app)

# -------------------------------
# MODEL CREATION
# -------------------------------
def build_model(input_shape=(LOOK_BACK, 1)):
    model = Sequential([
        LSTM(32, return_sequences=True, input_shape=input_shape),
        Dropout(0.1),
        LSTM(32),
        Dropout(0.1),
        Dense(1)
    ])
    model.compile(optimizer='adam', loss='mse')
    return model

# -------------------------------
# CREATE SEQUENCES
# -------------------------------
def create_sequences(data, look_back):
    X, Y = [], []
    for i in range(look_back, len(data)):
        X.append(data[i - look_back:i, 0])
        Y.append(data[i, 0])
    return np.array(X), np.array(Y)

# -------------------------------
# FORECAST FUNCTION
# -------------------------------
def forecast_stock(df):
    """Forecast next FORECAST_DAYS prices based on 'Close' prices."""
    df = df[['Close']].dropna()
    if df.empty or len(df) <= LOOK_BACK:
        return {"error": f"Not enough data to forecast. Need at least {LOOK_BACK + 1} days."}, 400

    data = df.values
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(data)

    X_train, Y_train = create_sequences(scaled_data, LOOK_BACK)
    X_train = X_train.reshape((X_train.shape[0], X_train.shape[1], 1))

    # Build and train model
    model = build_model()
    model.fit(X_train, Y_train, epochs=12, batch_size=64, verbose=0)

    # Forecast
    forecast_input = scaled_data[-LOOK_BACK:].copy()
    predicted_scaled = []
    predicted_dates = []
    last_date = df.index[-1]

    for _ in range(FORECAST_DAYS):
        batch = forecast_input[-LOOK_BACK:].reshape(1, LOOK_BACK, 1)
        next_val = float(model(batch, training=False).numpy()[0, 0])
        forecast_input = np.append(forecast_input, [[next_val]], axis=0)
        predicted_scaled.append(next_val)

        # Compute next trading day (skip weekends)
        next_date = last_date
        while True:
            next_date += pd.Timedelta(days=1)
            if next_date.weekday() < 5:
                break
        predicted_dates.append(next_date)
        last_date = next_date

    actual_predictions = scaler.inverse_transform(np.array(predicted_scaled).reshape(-1, 1))

    # Format response
    result = {
        "last_price": float(scaler.inverse_transform(scaled_data[-1].reshape(-1, 1))[0][0]),
        "last_date": df.index[-1].strftime('%Y-%m-%d'),
        "day_7": {
            "date": predicted_dates[6].strftime('%Y-%m-%d'),
            "price": float(actual_predictions[6][0])
        },
        "day_14": {
            "date": predicted_dates[13].strftime('%Y-%m-%d'),
            "price": float(actual_predictions[13][0])
        }
    }
    return result, 200

# -------------------------------
# PREDICT RESOURCE
# -------------------------------
class Predict(Resource):
    def get(self):
        # Instead of reqparse, just read query param directly
        stock_ticker = request.args.get('stock', '').upper()

        if not stock_ticker:
            return {"error": "Stock ticker is required"}, 400

        START_DATE = '2015-01-01'
        END_DATE = datetime.now().strftime('%Y-%m-%d')

        # Download stock data safely
        df = yf.download(stock_ticker, start=START_DATE, end=END_DATE, progress=False, auto_adjust=True)
        if df.empty:
            return {"error": f"Ticker '{stock_ticker}' not found or has no data"}, 400

        try:
            result, status = forecast_stock(df)
            return result, status
        except Exception as e:
            import traceback
            print("❌ Prediction error:", e)
            traceback.print_exc()
            return {"error": f"Prediction failed: {str(e)}"}, 500
