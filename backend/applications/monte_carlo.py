# -- coding: utf-8 --
"""
📊 Monte Carlo Simulation API for Portfolio (Equal Weights)
→ Accepts list of stocks, performs Monte Carlo with equal allocation
→ Returns expected return, volatility, and 5% worst-case
"""

from flask import Flask, request
from flask_restful import Api, Resource
import numpy as np
import pandas as pd
import yfinance as yf
from scipy.stats import norm

# -------------------------------
# CONFIG
# -------------------------------
NUM_SIMULATIONS = 10000
TRADING_DAYS = 252

# -------------------------------
# HELPER FUNCTION
# -------------------------------
def monte_carlo_portfolio(stocks, start_date='2021-01-01'):
    if not stocks or len(stocks) == 0:
        return {"error": "No stocks provided"}, 400

    # Assign equal weights
    weights = np.ones(len(stocks)) / len(stocks)

    # Fetch data
    try:
        data = yf.download(stocks, start=start_date, progress=False, auto_adjust=True)
        if isinstance(data.columns, pd.MultiIndex):
            data = data['Close']
        elif 'Close' in data.columns:
            data = data[['Close']]
        else:
            raise ValueError("Unexpected data structure from yfinance")
        if data.empty:
            return {"error": "No data downloaded. Check tickers or internet connection."}, 400
    except Exception as e:
        return {"error": f"Failed to download data: {str(e)}"}, 500

    # Calculate returns
    returns = data.pct_change().dropna()
    log_returns = np.log1p(returns)
    mean_returns = log_returns.mean()
    cov_matrix = log_returns.cov()

    # Portfolio drift and volatility
    portfolio_mean = np.dot(mean_returns, weights)
    portfolio_std_dev = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
    drift = portfolio_mean - 0.5 * portfolio_std_dev**2

    # Monte Carlo simulation
    final_values = np.zeros(NUM_SIMULATIONS)
    for i in range(NUM_SIMULATIONS):
        z = norm.ppf(np.random.rand(TRADING_DAYS))
        daily_returns = np.exp(drift + portfolio_std_dev * z)
        final_values[i] = daily_returns.prod()

    # Analysis
    P_final_mean = np.mean(final_values) - 1.0
    P_volatility = np.std(final_values)
    P_worst_5_percent = np.percentile(final_values, 5) - 1.0

    if P_final_mean > 0.15:
        conclusion = "High expected profitability (with possible high risk)."
    elif P_final_mean > 0.05 and P_volatility < 0.5:
        conclusion = "Moderate profitability with managed risk."
    elif P_final_mean <= 0:
        conclusion = "Negative expected return — reconsider your allocation."
    else:
        conclusion = "Low expected return; check if risk is worth it."

    result = {
        "stocks": stocks,
        "weights": weights.tolist(),
        "expected_return": round(P_final_mean, 4),
        "volatility": round(P_volatility, 4),
        "worst_5_percent": round(P_worst_5_percent, 4),
        "conclusion": conclusion
    }

    return result, 200

# -------------------------------
# FLASK APP
# -------------------------------
app = Flask(__name__)
api = Api(app)

class MonteCarlo(Resource):
    def post(self):
        data = request.get_json(force=True)
        stocks = data.get("stocks")
        return monte_carlo_portfolio(stocks)

# -- coding: utf-8 --
"""
📊 Monte Carlo Simulation API for Portfolio (Equal Weights, % Output)
→ Accepts list of stocks, performs Monte Carlo with equal allocation
→ Returns expected return, volatility, and 5% worst-case in %
"""

from flask import Flask, request
from flask_restful import Api, Resource
import numpy as np
import pandas as pd
import yfinance as yf
from scipy.stats import norm

# -------------------------------
# CONFIG
# -------------------------------
NUM_SIMULATIONS = 10000
TRADING_DAYS = 252

# -------------------------------
# HELPER FUNCTION
# -------------------------------
def monte_carlo_portfolio(stocks, start_date='2021-01-01'):
    if not stocks or len(stocks) == 0:
        return {"error": "No stocks provided"}, 400

    # Assign equal weights
    weights = np.ones(len(stocks)) / len(stocks)

    # Fetch data
    try:
        data = yf.download(stocks, start=start_date, progress=False, auto_adjust=True)
        if isinstance(data.columns, pd.MultiIndex):
            data = data['Close']
        elif 'Close' in data.columns:
            data = data[['Close']]
        else:
            raise ValueError("Unexpected data structure from yfinance")
        if data.empty:
            return {"error": "No data downloaded. Check tickers or internet connection."}, 400
    except Exception as e:
        return {"error": f"Failed to download data: {str(e)}"}, 500

    # Calculate returns
    returns = data.pct_change().dropna()
    log_returns = np.log1p(returns)
    mean_returns = log_returns.mean()
    cov_matrix = log_returns.cov()

    # Portfolio drift and volatility
    portfolio_mean = np.dot(mean_returns, weights)
    portfolio_std_dev = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
    drift = portfolio_mean - 0.5 * portfolio_std_dev**2

    # Monte Carlo simulation
    final_values = np.zeros(NUM_SIMULATIONS)
    for i in range(NUM_SIMULATIONS):
        z = norm.ppf(np.random.rand(TRADING_DAYS))
        daily_returns = np.exp(drift + portfolio_std_dev * z)
        final_values[i] = daily_returns.prod()

    # Analysis (convert to %)
    P_final_mean = (np.mean(final_values) - 1.0) * 100
    P_volatility = np.std(final_values) * 100
    P_worst_5_percent = (np.percentile(final_values, 5) - 1.0) * 100

    if P_final_mean > 15:
        conclusion = "High expected profitability (with possible high risk)."
    elif P_final_mean > 5 and P_volatility < 50:
        conclusion = "Moderate profitability with managed risk."
    elif P_final_mean <= 0:
        conclusion = "Negative expected return — reconsider your allocation."
    else:
        conclusion = "Low expected return; check if risk is worth it."

    result = {
        "stocks": stocks,
        "weights": (weights * 100).round(2).tolist(),  # show weights in %
        "expected_return_percent": round(P_final_mean, 2),
        "volatility_percent": round(P_volatility, 2),
        "worst_5_percent_percent": round(P_worst_5_percent, 2),
        "conclusion": conclusion
    }

    return result, 200

