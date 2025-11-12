from flask_restful import Resource, reqparse
from flask import jsonify, request, make_response
from flask_security import hash_password, utils, auth_token_required, current_user
from applications.user_datastore import user_datastore
from applications.database import db
from applications.models import User, Watchlist, PortfolioHolding, PortfolioSnapshot, InvestmentGoal 
from applications.portfolio_analyzer import PortfolioAnalyzer
from sqlalchemy.sql import exists
from sqlalchemy.exc import IntegrityError
import uuid
import pandas as pd
import yfinance as yf

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
    """API endpoint for new user registration."""
    def post(self):
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if not username or not email or not password:
            return make_response(jsonify({'message': 'Username, email, and password are required'}), 400)

        try:
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

        except Exception:
            db.session.rollback()
            return make_response(jsonify({'message': 'Registration failed due to server error'}), 500)

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
class StockAnalyzer(Resource):
    """
    API resource fetching rich data using yfinance (for robustness).
    Endpoint: /api/v1/analyze?ticker=<SYMBOL>&exchange=NS
    """
    def get(self):
        try:
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

            analysis_data = {
                'ticker': info.get('symbol', yf_symbol),
                'company_name': info.get('longName', info.get('shortName', ticker_symbol)),
                'exchange': info.get('exchange', exchange_suffix),
                
                'last_price': info.get('regularMarketPrice'),
                'previous_close': info.get('previousClose'),
                'open_price': info.get('regularMarketOpen'),
                'day_high': info.get('regularMarketDayHigh'),
                'day_low': info.get('regularMarketDayLow'),
                'volume': info.get('regularMarketVolume'),
                'change_percent': info.get('regularMarketChangePercent'),

                'market_cap': info.get('marketCap'), 
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'employees': info.get('fullTimeEmployees'),
                'summary': info.get('longBusinessSummary'),
            }

            for key, value in analysis_data.items():
                if pd.isna(value) or value is None or value == "":
                    analysis_data[key] = 'N/A'
            
            # Add historical data for chart
            try:
                hist = ticker.history(period="1y")
                if not hist.empty:
                    chart_data = []
                    for date, row in hist.iterrows():
                        chart_data.append({
                            'date': date.strftime('%Y-%m-%d'),
                            'open': float(row['Open']),
                            'high': float(row['High']),
                            'low': float(row['Low']),
                            'close': float(row['Close']),
                            'volume': int(row['Volume'])
                        })
                    analysis_data['historical_data'] = chart_data
            except Exception:
                analysis_data['historical_data'] = []
                    
            return jsonify(analysis_data)

        except Exception:
            return make_response(jsonify({'message': 'Failed to fetch data. The external financial service may be unavailable or blocking requests.'}), 503)


# --- PORTFOLIO MANAGEMENT RESOURCES ---

class PortfolioHoldings(Resource):
    """
    GET /api/v1/portfolio/holdings - List all holdings for a user
    POST /api/v1/portfolio/holdings - Add a new stock to portfolio
    """
    def get(self, user_id):
        """Get all portfolio holdings for a user"""
        try:
            from applications.models import PortfolioHolding
            
            holdings = PortfolioHolding.query.filter_by(user_id=user_id).all()
            
            if not holdings:
                return make_response(jsonify({'message': 'No holdings found', 'holdings': []}), 200)
            
            holdings_data = [holding.to_dict() for holding in holdings]
            total_value = sum(h['current_value'] for h in holdings_data)
            total_invested = sum(h['total_invested'] for h in holdings_data)
            total_gain_loss = total_value - total_invested
            
            return make_response(jsonify({
                'holdings': holdings_data,
                'summary': {
                    'total_value': round(total_value, 2),
                    'total_invested': round(total_invested, 2),
                    'total_gain_loss': round(total_gain_loss, 2),
                    'total_gain_loss_percent': round((total_gain_loss / total_invested * 100), 2) if total_invested != 0 else 0
                }
            }), 200)
        except Exception as e:
            return make_response(jsonify({'message': f'Error retrieving holdings: {str(e)}'}), 500)

    def post(self, user_id):
        """Add a new stock holding to portfolio"""
        try:
            from applications.models import PortfolioHolding
            
            data = request.get_json()
            symbol = data.get('symbol', '').upper()
            quantity = float(data.get('quantity', 0))
            purchase_price = float(data.get('purchase_price', 0))
            
            if not symbol or quantity <= 0 or purchase_price <= 0:
                return make_response(jsonify({'message': 'Symbol, quantity, and purchase_price are required and must be positive'}), 400)
            
            # Fetch current price from yfinance
            try:
                # Smart ticker format: if symbol is <= 5 chars, assume Indian stock with .NS
                # Otherwise use as-is (for US stocks like AAPL)
                exchange = data.get('exchange', 'NS')  # Default to NSE for Indian stocks
                if exchange.upper() in ['NS', 'BO']:
                    yf_symbol = f"{symbol}.{exchange.upper()}"
                else:
                    yf_symbol = symbol
                
                ticker = yf.Ticker(yf_symbol)
                current_data = ticker.info
                current_price = current_data.get('currentPrice') or current_data.get('regularMarketPrice', purchase_price)
            except Exception as fetch_error:
                print(f"[PRICE_FETCH_ERROR] {fetch_error}")
                current_price = purchase_price  # Fallback to purchase price if fetch fails
            
            current_value = quantity * current_price
            
            # Check if holding already exists
            existing = PortfolioHolding.query.filter_by(user_id=user_id, symbol=symbol).first()
            
            if existing:
                # Update existing holding (average the purchase price)
                new_quantity = existing.quantity + quantity
                new_purchase_price = ((existing.quantity * existing.purchase_price) + (quantity * purchase_price)) / new_quantity
                existing.quantity = new_quantity
                existing.purchase_price = new_purchase_price
                existing.current_value = new_quantity * current_price
            else:
                # Create new holding
                holding = PortfolioHolding(
                    user_id=user_id,
                    symbol=symbol,
                    quantity=quantity,
                    purchase_price=purchase_price,
                    current_value=current_value
                )
                db.session.add(holding)
            
            db.session.commit()
            return make_response(jsonify({'message': 'Holding added successfully', 'holding': (existing or holding).to_dict()}), 201)
            
        except ValueError:
            return make_response(jsonify({'message': 'Invalid quantity or price format'}), 400)
        except Exception as e:
            db.session.rollback()
            return make_response(jsonify({'message': f'Error adding holding: {str(e)}'}), 500)


class PortfolioHoldingDetail(Resource):
    """
    DELETE /api/v1/portfolio/holdings/<id> - Remove a holding from portfolio
    PUT /api/v1/portfolio/holdings/<id> - Update a holding
    """
    def delete(self, user_id, holding_id):
        """Remove a stock holding from portfolio"""
        try:
            from applications.models import PortfolioHolding
            
            holding = PortfolioHolding.query.filter_by(id=holding_id, user_id=user_id).first()
            
            if not holding:
                return make_response(jsonify({'message': 'Holding not found'}), 404)
            
            db.session.delete(holding)
            db.session.commit()
            return make_response(jsonify({'message': 'Holding removed successfully'}), 200)
        except Exception as e:
            db.session.rollback()
            return make_response(jsonify({'message': f'Error deleting holding: {str(e)}'}), 500)
    
    def put(self, user_id, holding_id):
        """Update a stock holding"""
        try:
            from applications.models import PortfolioHolding
            
            data = request.get_json()
            holding = PortfolioHolding.query.filter_by(id=holding_id, user_id=user_id).first()
            
            if not holding:
                return make_response(jsonify({'message': 'Holding not found'}), 404)
            
            if 'quantity' in data:
                holding.quantity = float(data['quantity'])
            if 'purchase_price' in data:
                holding.purchase_price = float(data['purchase_price'])
            if 'current_value' in data:
                holding.current_value = float(data['current_value'])
            
            db.session.commit()
            return make_response(jsonify({'message': 'Holding updated successfully', 'holding': holding.to_dict()}), 200)
        except Exception as e:
            db.session.rollback()
            return make_response(jsonify({'message': f'Error updating holding: {str(e)}'}), 500)


class PortfolioAnalysis(Resource):
    """
    GET /api/v1/portfolio/analysis/<user_id> - Get complete portfolio analysis
    """
    def get(self, user_id):
        """Get complete portfolio analysis with health scores, diversification, risk, performance"""
        try:
            analyzer = PortfolioAnalyzer(user_id)
            analysis = analyzer.get_complete_analysis()
            
            # Save a snapshot for historical tracking
            analyzer.save_snapshot()
            
            return make_response(jsonify(analysis), 200)
        except Exception as e:
            return make_response(jsonify({'message': f'Error analyzing portfolio: {str(e)}'}), 500)


class PortfolioPerformance(Resource):
    """
    GET /api/v1/portfolio/performance/<user_id> - Get historical portfolio performance
    """
    def get(self, user_id):
        """Get historical performance data for charts"""
        try:
            days = request.args.get('days', 30, type=int)
            analyzer = PortfolioAnalyzer(user_id)
            
            history = analyzer.get_performance_history(days=days)
            current_analysis = analyzer.get_complete_analysis()
            
            return make_response(jsonify({
                'history': history,
                'current_portfolio': current_analysis['portfolio_data'],
                'days': days
            }), 200)
        except Exception as e:
            return make_response(jsonify({'message': f'Error retrieving performance: {str(e)}'}), 500)


class PortfolioGoals(Resource):
    """
    POST /api/v1/portfolio/goals/<user_id> - Create investment goal
    GET /api/v1/portfolio/goals/<user_id> - List all goals
    """
    def post(self, user_id):
        """Create a new investment goal"""
        try:
            data = request.get_json()
            goal_name = data.get('goal_name', '').strip()
            target_amount = float(data.get('target_amount', 0))
            target_date_str = data.get('target_date')  # Expected format: YYYY-MM-DD
            
            if not goal_name or target_amount <= 0 or not target_date_str:
                return make_response(jsonify({'message': 'goal_name, target_amount, and target_date are required'}), 400)
            
            import datetime
            target_date = datetime.datetime.strptime(target_date_str, '%Y-%m-%d')
            
            goal = InvestmentGoal(
                user_id=user_id,
                goal_name=goal_name,
                description=data.get('description'),
                target_amount=target_amount,
                current_amount=float(data.get('current_amount', 0)),
                target_date=target_date
            )
            
            db.session.add(goal)
            db.session.commit()
            
            return make_response(jsonify({'message': 'Goal created successfully', 'goal': goal.to_dict()}), 201)
        except ValueError as e:
            return make_response(jsonify({'message': f'Invalid date format. Use YYYY-MM-DD: {str(e)}'}), 400)
        except Exception as e:
            db.session.rollback()
            return make_response(jsonify({'message': f'Error creating goal: {str(e)}'}), 500)
    
    def get(self, user_id):
        """Get all investment goals for user"""
        try:
            goals = InvestmentGoal.query.filter_by(user_id=user_id).all()
            goals_data = [goal.to_dict() for goal in goals]
            
            return make_response(jsonify({
                'goals': goals_data,
                'total_goals': len(goals_data)
            }), 200)
        except Exception as e:
            return make_response(jsonify({'message': f'Error retrieving goals: {str(e)}'}), 500)


class PortfolioGoalDetail(Resource):
    """
    PUT /api/v1/portfolio/goals/<user_id>/<goal_id> - Update goal
    DELETE /api/v1/portfolio/goals/<user_id>/<goal_id> - Delete goal
    """
    def put(self, user_id, goal_id):
        """Update an investment goal"""
        try:
            goal = InvestmentGoal.query.filter_by(id=goal_id, user_id=user_id).first()
            
            if not goal:
                return make_response(jsonify({'message': 'Goal not found'}), 404)
            
            data = request.get_json()
            
            if 'goal_name' in data:
                goal.goal_name = data['goal_name']
            if 'current_amount' in data:
                goal.current_amount = float(data['current_amount'])
            if 'target_amount' in data:
                goal.target_amount = float(data['target_amount'])
            if 'description' in data:
                goal.description = data['description']
            
            db.session.commit()
            return make_response(jsonify({'message': 'Goal updated successfully', 'goal': goal.to_dict()}), 200)
        except Exception as e:
            db.session.rollback()
            return make_response(jsonify({'message': f'Error updating goal: {str(e)}'}), 500)
    
    def delete(self, user_id, goal_id):
        """Delete an investment goal"""
        try:
            goal = InvestmentGoal.query.filter_by(id=goal_id, user_id=user_id).first()
            
            if not goal:
                return make_response(jsonify({'message': 'Goal not found'}), 404)
            
            db.session.delete(goal)
            db.session.commit()
            
            return make_response(jsonify({'message': 'Goal deleted successfully'}), 200)
        except Exception as e:
            db.session.rollback()
            return make_response(jsonify({'message': f'Error deleting goal: {str(e)}'}), 500)

