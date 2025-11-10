from flask_restful import Resource, reqparse
from flask import jsonify, request, make_response
from flask_security import hash_password, utils, auth_token_required, current_user
from applications.user_datastore import user_datastore
from applications.database import db
from applications.models import User, Watchlist 
from sqlalchemy.sql import exists
from sqlalchemy.exc import IntegrityError
import uuid
import pandas as pd
import yfinance as yf

# --- Required Imports (Ensure these are at the top of your file) ---
import requests
import feedparser
from dateutil import parser as dateparser
from datetime import datetime
# ... (existing imports like Resource, reqparse, jsonify, yf, etc.)

# --- Global Parsers ---
analyzer_parser = reqparse.RequestParser()
analyzer_parser.add_argument(
    'ticker', 
    type=str, 
    required=True, 
    help='Stock ticker symbol is required', 
    location='args',
    case_sensitive=False 
)
analyzer_parser.add_argument(
    'exchange', 
    type=str, 
    required=False, 
    default='NS', 
    help='Exchange symbol suffix (e.g., NS)', 
    location='args',
    case_sensitive=False
)

add_watchlist_parser = reqparse.RequestParser()
add_watchlist_parser.add_argument('user_id', type=int, required=True, help='User ID is required', location='json')
add_watchlist_parser.add_argument('ticker', type=str, required=True, help='Ticker is required', location='json')
add_watchlist_parser.add_argument('notes', type=str, required=False, location='json')


# --- AUTHENTICATION RESOURCES ---
class ValidUser(Resource):
    """API endpoint to check if a username or email is already registered."""
    def post(self):
        data = request.get_json()
        identifier = data.get('username') or data.get('email')

        if not identifier:
            return make_response(jsonify({'message': 'Username or Email is required'}), 400)

        user = user_datastore.find_user(username=identifier) or user_datastore.find_user(email=identifier)

        if user:
            return make_response(jsonify({'message': 'Identifier already exists'}), 409)
        return make_response(jsonify({'message': 'Identifier is available'}), 200)

class Registration(Resource):
    def post(self):
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        if not username or not email or not password:
            return make_response(jsonify({'message': 'All fields are required'}), 400)

        if user_datastore.find_user(email=email):
            return make_response(jsonify({'message': 'Email already registered'}), 400)

        try:
            if not user_datastore.find_role("user"):
                user_datastore.create_role(name="user")
                db.session.commit()

            user = user_datastore.create_user(
                username=username,
                email=email,
                password=hash_password(password),
                active=True,
                roles=["user"],
                fs_uniquifier=str(uuid.uuid4())
            )
            db.session.commit()
            return make_response(jsonify({'message': 'User registered successfully'}), 201)

        except Exception as e:
            db.session.rollback()
            print(f"❌ Registration error: {e}")
            return make_response(jsonify({'message': 'Registration failed', 'error': str(e)}), 500)

class Login(Resource):
    """API endpoint for user login."""
    def post(self):
        data = request.get_json()
        identifier = data.get('username') or data.get('email')
        password = data.get('password')

        if not identifier or not password:
            return make_response(jsonify({'message': 'Username/Email and password are required'}), 400)

        user = user_datastore.find_user(username=identifier) or user_datastore.find_user(email=identifier)

        if not user:
            return make_response(jsonify({'message': 'Invalid credentials'}), 401)

        # FIX: Truncate password before verification to prevent bcrypt ValueError
        password_bytes = password.encode('utf-8')
        safe_password = password_bytes[:72] 
        
        if not utils.verify_password(safe_password, user.password):
            return make_response(jsonify({'message': 'Invalid credentials'}), 401) 
        
        if not user.active:
            return make_response(jsonify({'message': 'Account is inactive. Please contact support.'}), 403)

        try:
            auth_token = user.get_auth_token()
            response_data = {
                'message': 'Login successful',
                'token': auth_token,
                'user': {'id': user.id, 'username': user.username, 'email': user.email}
            }
            return make_response(jsonify(response_data), 200)

        except Exception:
            return make_response(jsonify({'message': 'Login failed due to server error'}), 500)

class Logout(Resource):
    """API endpoint for user logout."""
    @auth_token_required
    def post(self):
        return make_response(jsonify({'message': 'Logged out successfully'}), 200)

# -------------------------------------------------------------
# WATCHLIST CRUD RESOURCES
# -------------------------------------------------------------

class WatchlistCheck(Resource):
    """GET /has_watchlist/<int:user_id> -> returns boolean if records exist."""
    def get(self, user_id):
        has_records = db.session.query(
            exists().where(Watchlist.user_id == user_id)
        ).scalar()
        
        return jsonify({
            'user_id': user_id,
            'has_watchlist_records': has_records
        })

class UserWatchlist(Resource):
    """GET /watchlist/<int:user_id> -> fetches all watchlist records."""
    def get(self, user_id):
        watchlist_items = Watchlist.query.filter_by(user_id=user_id).all()
        watchlist_data = [item.to_dict() for item in watchlist_items]
        
        return jsonify({
            'user_id': user_id,
            'count': len(watchlist_data),
            'watchlist': watchlist_data
        })

from flask_restful import Resource, reqparse
from flask import request, jsonify, make_response
from applications.database import db
from applications.models import Watchlist, User
from sqlalchemy.exc import IntegrityError
import datetime

# Parser for validating input JSON
add_watchlist_parser = reqparse.RequestParser()
add_watchlist_parser.add_argument('ticker', type=str, required=True, help='Ticker is required', location='json')
add_watchlist_parser.add_argument('notes', type=str, required=False, location='json')

class AddToWatchlist(Resource):
    """
    POST /api/v1/watchlist/add
    Header: {"user-id": <int>}
    Body (JSON): {"ticker": "AAPL", "notes": "Apple Inc"}
    """
    def post(self):
        # Extract user ID from request header
        user_id = request.headers.get('user-id')

        if not user_id:
            return make_response(jsonify({'message': 'User ID header is required'}), 400)

        try:
            user_id = int(user_id)
        except ValueError:
            return make_response(jsonify({'message': 'Invalid User ID format'}), 400)

        # Check if user exists
        user = User.query.get(user_id)
        if not user:
            return make_response(jsonify({'message': f'User with ID {user_id} not found'}), 404)

        # Parse JSON body
        args = add_watchlist_parser.parse_args()
        ticker = args.get('ticker').upper().strip()
        notes = args.get('notes')

        if not ticker:
            return make_response(jsonify({'message': 'Ticker cannot be empty'}), 400)

        # Check for duplicates
        existing = Watchlist.query.filter_by(user_id=user_id, ticker=ticker).first()
        if existing:
            return make_response(jsonify({'message': f'Ticker "{ticker}" is already in your watchlist'}), 409)

        try:
            new_item = Watchlist(
                user_id=user_id,
                ticker=ticker,
                notes=notes,
                added_at=datetime.datetime.utcnow()
            )
            db.session.add(new_item)
            db.session.commit()

            return make_response(jsonify({
                'message': 'Ticker added successfully',
                'watchlist_item': new_item.to_dict()
            }), 201)

        except IntegrityError:
            db.session.rollback()
            return make_response(jsonify({'message': 'Duplicate entry not allowed'}), 409)
        except Exception as e:
            db.session.rollback()
            print("Error:", e)
            return make_response(jsonify({'message': 'Server error while adding to watchlist'}), 500)


class WatchlistItemDeletion(Resource):
    """
    DELETE /api/v1/watchlist/<int:item_id> -> deletes a single watchlist item.
    """
    # @auth_token_required would be used here in a production app
    def delete(self, item_id):
        # 1. Find the item
        item = Watchlist.query.get(item_id)
        
        if not item:
            return make_response(jsonify({'message': f'Watchlist item with ID {item_id} not found.'}), 404)
            
        # 2. Delete and commit
        try:
            db.session.delete(item)
            db.session.commit()
            
            return make_response(jsonify({
                'message': f'Watchlist item {item_id} ({item.ticker}) deleted successfully.'
            }), 200)

        except Exception:
            db.session.rollback()
            return make_response(jsonify({'message': 'Failed to delete item due to a server error.'}), 500)


# -------------------------------------------------------------
# STOCK ANALYZER (Using yfinance)
# -------------------------------------------------------------
# --- Global Headers to prevent scraping blocks ---
RSS_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

class StockAnalyzer(Resource):
    """
    API resource fetching rich data using yfinance and news (via robust Google News RSS).
    """

    @staticmethod
    def _fetch_google_news(query, count=4):
        """Internal method to fetch and parse Google News RSS for a query."""
        try:
            # Construct the Google News RSS URL for a search query (India, English)
            rss_url = f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"
            
            # Make the network request with headers for stability
            response = requests.get(rss_url, headers=RSS_HEADERS, timeout=15)
            response.raise_for_status() # Raise HTTPError for bad status codes (4xx or 5xx)

            feed = feedparser.parse(response.content)
            news_list = []

            if feed.entries:
                for entry in feed.entries[:count]:
                    published_at_str = 'N/A'
                    
                    if getattr(entry, 'published', None):
                        try:
                            # Use dateutil for robustly parsing various RSS date formats
                            published_dt = dateparser.parse(entry.published)
                            published_at_str = published_dt.strftime('%Y-%m-%d %H:%M:%S')
                        except Exception:
                            published_at_str = 'N/A'
                    
                    news_list.append({
                        'title': getattr(entry, 'title', 'Headline Unavailable'),
                        'link': getattr(entry, 'link', '#'),
                        'source': getattr(entry.source, 'title', 'N/A'),
                        'type': 'RSS',
                        'published_at': published_at_str,
                    })
                
            return news_list if news_list else [{'message': f'No recent Google News found for "{query}".'}]

        except requests.exceptions.RequestException as e:
            # Catch network errors (ConnectionError, Timeout, HTTPError)
            print(f"ERROR: Network/Scraping failure during news fetch: {e}")
            return [{'message': 'Failed to retrieve news due to network connection or external block. (Check Python logs)'}]
        
        except Exception as e:
            # Catch general parsing errors
            print(f"ERROR: General news parsing failure: {e}")
            return [{'message': 'Failed to retrieve news due to data processing error.'}]


    def get(self):
        try:
            # --- Argument Parsing (Unchanged) ---
            args = analyzer_parser.parse_args()
            ticker_symbol = args['ticker'].upper()
            exchange_suffix = args['exchange'].upper()
            yf_symbol = f"{ticker_symbol}.{exchange_suffix}"
            
        except Exception:
            return make_response(jsonify({'message': 'Missing required query parameter: ticker.'}), 400)

        try:
            ticker = yf.Ticker(yf_symbol)
            info = ticker.info
            
            if 'regularMarketPrice' not in info and 'symbol' not in info:
                return make_response(jsonify({'message': f'Ticker symbol "{yf_symbol}" not found. Check symbol accuracy.'}), 404)

            # --- 1. Fetch Company Name for News Search Query ---
            company_name = info.get('longName', ticker_symbol)
            
            # KEY FIX: Removed the word "stock" to broaden the search and get fresher general news
            news_query = f"{company_name}" 

            # --- 2. Execute News Headlines Fetch ---
            news_data = self._fetch_google_news(news_query, count=4) 
            
            # --- 3. Extract Stock Analysis Data (Unchanged) ---
            # --- 3. Extract Stock Analysis Data (FIXED KEYS) ---
            analysis_data = {
                'ticker': info.get('symbol', yf_symbol),
                'company_name': company_name,
                'exchange': info.get('exchange', exchange_suffix),
                
                # PRICE/VOLUME FIELDS
                'last_price': info.get('regularMarketPrice') or info.get('currentPrice'),
                'previous_close': info.get('previousClose') or info.get('regularMarketPreviousClose'),

                # FIX: Use multiple keys for Volatility/Volume fields
                'open_price': info.get('regularMarketOpen') or info.get('open'),
                'day_high': info.get('regularMarketDayHigh') or info.get('dayHigh'),
                'day_low': info.get('regularMarketDayLow') or info.get('dayLow'),
                
                # FIX: Check multiple volume fields
                'volume': info.get('regularMarketVolume') or info.get('volume') or info.get('averageVolume'),

                # FIX: Check multiple Change/Percent fields
                'change_percent': info.get('regularMarketChangePercent') or info.get('52WeekChange') or 'N/A',

                # FUNDAMENTAL FIELDS
                'market_cap': info.get('marketCap') or info.get('enterpriseValue'), 
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'employees': info.get('fullTimeEmployees'),
                'summary': info.get('longBusinessSummary'),
            }

            # Your final cleanup loop handles the conversion of None/pd.isna to 'N/A'
            for key, value in analysis_data.items():
                if pd.isna(value) or value is None or value == 0 or value == "": # Added value == 0 check
                    analysis_data[key] = 'N/A'
            # --- 4. Combine and Return Data ---
            response_payload = {
                'analysis': analysis_data,
                'news_headlines': news_data
            }
                    
            return jsonify(response_payload)

        except Exception as e:
            print(f"StockAnalyzer Fatal Error (outer block): {e}")
            return make_response(jsonify({'message': 'Failed to fetch data. The external financial service may be unavailable or blocking requests.'}), 503)