import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from sklearn.preprocessing import MinMaxScaler
import yfinance as yf
from datetime import datetime, timedelta

# -------------------------------
# 1️⃣ CONFIGURATION
# -------------------------------
STOCK_TICKER = 'TCS.NS'
START_DATE = '2015-01-01'
END_DATE = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
LOOK_BACK = 60
FORECAST_DAYS = 14

print("--- ⚙️ Config ---")
print(f"Stock: {STOCK_TICKER}")
print(f"Data until: {END_DATE}")
print("-" * 30)

# -------------------------------
# 2️⃣ GPU CHECK (Metal Acceleration)
# -------------------------------
gpus = tf.config.list_physical_devices('GPU')
if gpus:
    print(f"✅ GPU Active: {gpus[0].name}")
else:
    print("⚠️ GPU not detected — using CPU")

# -------------------------------
# 3️⃣ DATA LOADING
# -------------------------------
print(f"📥 Downloading {STOCK_TICKER}...")
df = yf.download(STOCK_TICKER, start=START_DATE, end=END_DATE, progress=False)
if df.empty:
    raise ValueError("No stock data downloaded!")

data = df['Close'].values.reshape(-1, 1)
scaler = MinMaxScaler(feature_range=(0, 1))
scaled_data = scaler.fit_transform(data)

# -------------------------------
# 4️⃣ SEQUENCE CREATION (Vectorized)
# -------------------------------
def create_sequences(data, look_back):
    X, Y = [], []
    for i in range(look_back, len(data)):
        X.append(data[i - look_back:i, 0])
        Y.append(data[i, 0])
    return np.array(X), np.array(Y)

X_train, Y_train = create_sequences(scaled_data, LOOK_BACK)
X_train = X_train.reshape((X_train.shape[0], X_train.shape[1], 1))
print(f"✅ Training shape: {X_train.shape}")

# -------------------------------
# 5️⃣ MODEL (Simplified + Fast)
# -------------------------------
model = Sequential([
    LSTM(32, return_sequences=True, input_shape=(LOOK_BACK, 1)),
    Dropout(0.1),
    LSTM(32),
    Dropout(0.1),
    Dense(1)
])

model.compile(optimizer='adam', loss='mse')

# -------------------------------
# 6️⃣ TRAINING (Accelerated)
# -------------------------------
# Lower epochs, larger batch, GPU-friendly
print("🚀 Training LSTM...")
history = model.fit(
    X_train,
    Y_train,
    epochs=12,
    batch_size=64,
    verbose=0
)

print("✅ Training complete.")
print("-" * 30)

# -------------------------------
# 7️⃣ FORECASTING (Vectorized)
# -------------------------------
@tf.function
def predict_next(input_batch):
    return model(input_batch, training=False)

forecast_input = scaled_data[-LOOK_BACK:].copy()
predicted_scaled = []

for _ in range(FORECAST_DAYS):
    batch = forecast_input[-LOOK_BACK:].reshape(1, LOOK_BACK, 1)
    next_pred = predict_next(batch)
    next_value = next_pred.numpy()[0, 0]
    forecast_input = np.append(forecast_input, [[next_value]], axis=0)
    predicted_scaled.append(next_value)

# -------------------------------
# 8️⃣ OUTPUT RESULTS
# -------------------------------
actual_predictions = scaler.inverse_transform(np.array(predicted_scaled).reshape(-1, 1))
last_price = scaler.inverse_transform(scaled_data[-1].reshape(-1, 1))[0][0]

print("\n--- ✅ Forecast ---")
print(f"Last Known Price ({df.index[-1].strftime('%Y-%m-%d')}): ₹{last_price:.2f}")
print(f"Predicted Price (Day 7): ₹{actual_predictions[6][0]:.2f}")
print(f"Predicted Price (Day 14): ₹{actual_predictions[13][0]:.2f}")
