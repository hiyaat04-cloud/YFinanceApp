"""AI Stock Advisor using Google Gemini API"""
from flask_restful import Resource, reqparse
from flask import request, jsonify, make_response
from flask_security import auth_token_required, current_user
import google.generativeai as genai
import yfinance as yf
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from backend folder
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Configure Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set. Add it to .env file")

genai.configure(api_key=GEMINI_API_KEY)

# Create model instance - Use gemini-2.5-flash (latest stable model)
model = genai.GenerativeModel('gemini-2.5-flash')

class AIStockAdvisor(Resource):
    """
    POST /api/v1/ai/analyze
    Analyze stock using AI and provide investment advice
    Body: {"ticker": "TCS", "question": "Should I buy this stock?"}
    """
    def post(self):
        data = request.get_json()
        ticker = data.get('ticker', '').upper()
        question = data.get('question', 'What is your analysis of this stock?')
        exchange = data.get('exchange', 'NS').upper()  # NS for NSE (Indian), O for NASDAQ, L for LSE, etc.

        if not ticker:
            return make_response(jsonify({'message': 'Ticker is required'}), 400)

        try:
            # Determine stock symbol format based on exchange
            # Indian stocks use .NS or .BO, US stocks don't need suffix
            indian_stocks = ['NS', 'BO']  # NSE and BSE
            us_stocks = ['O', 'L', 'V']  # NASDAQ, NYSE, AMEX
            
            if exchange in indian_stocks:
                yf_symbol = f"{ticker}.{exchange}"
            else:
                # For US stocks, use ticker as-is
                yf_symbol = ticker
            
            stock = yf.Ticker(yf_symbol)
            info = stock.info
            hist = stock.history(period="3mo")

            # Prepare context for AI
            stock_context = f"""
Stock: {info.get('symbol', ticker)}
Company: {info.get('longName', 'N/A')}
Current Price: ${info.get('regularMarketPrice', 'N/A')}
Previous Close: ${info.get('previousClose', 'N/A')}
Day High: ${info.get('regularMarketDayHigh', 'N/A')}
Day Low: ${info.get('regularMarketDayLow', 'N/A')}
Volume: {info.get('regularMarketVolume', 'N/A')}
Market Cap: ${info.get('marketCap', 'N/A')}
P/E Ratio: {info.get('trailingPE', 'N/A')}
Sector: {info.get('sector', 'N/A')}
Industry: {info.get('industry', 'N/A')}
52 Week High: ${info.get('fiftyTwoWeekHigh', 'N/A')}
52 Week Low: ${info.get('fiftyTwoWeekLow', 'N/A')}
            """

            # Create AI prompt
            ai_prompt = f"""You are an expert financial advisor. Analyze this stock data and answer the user's question.

{stock_context}

User Question: {question}

Provide a concise, professional analysis with:
1. Current market analysis
2. Key metrics interpretation
3. Risk assessment
4. Investment recommendation (BUY/HOLD/SELL)
5. Reasoning

Keep response under 300 words."""

            # Get AI response
            response = model.generate_content(ai_prompt)
            ai_analysis = response.text

            return make_response(jsonify({
                'ticker': ticker,
                'company_name': info.get('longName', ticker),
                'current_price': info.get('regularMarketPrice'),
                'ai_analysis': ai_analysis,
                'stock_data': {
                    'previous_close': info.get('previousClose'),
                    'day_high': info.get('regularMarketDayHigh'),
                    'day_low': info.get('regularMarketDayLow'),
                    'volume': info.get('regularMarketVolume'),
                    'market_cap': info.get('marketCap'),
                    'pe_ratio': info.get('trailingPE'),
                    'sector': info.get('sector'),
                }
            }), 200)

        except Exception as e:
            error_msg = str(e)
            print(f"[AI_ADVISOR_ERROR] {error_msg}")
            
            # Provide user-friendly error messages
            if "API key" in error_msg or "invalid" in error_msg.lower():
                return make_response(jsonify({'message': 'AI service error: Invalid or missing API key. Please check configuration.'}), 503)
            elif "No data" in error_msg or "not found" in error_msg.lower():
                return make_response(jsonify({'message': f'Stock {ticker} not found. Please check the ticker symbol and exchange.'}), 404)
            else:
                return make_response(jsonify({'message': f'AI Analysis failed: {error_msg}'}), 500)




class AIChatbot(Resource):
    """
    POST /api/v1/ai/chat
    General financial chat with AI, optionally with portfolio context
    Requires: Authentication token (from login)
    Body: {
        "message": "What should I know about investing?",
        "include_portfolio": true  # Optional - whether to include user's portfolio context
    }
    """
    method_decorators = [auth_token_required]
    def post(self):
        """Chat endpoint that uses authenticated user's portfolio context"""
        try:
            data = request.get_json()
        except Exception as e:
            print(f"[ERROR] Failed to parse JSON: {e}")
            data = {}
            
        message = data.get('message', '').strip()
        include_portfolio = data.get('include_portfolio', False)
        
        # Get user_id from authenticated user (not from JSON)
        from flask_security import current_user
        user_id = current_user.id
        
        print(f"[DEBUG] Authenticated user_id={user_id}, include_portfolio={include_portfolio}, message={message[:50] if message else 'EMPTY'}")

        if not message:
            return make_response(jsonify({'message': 'Message is required'}), 400)

        try:
            # Prepare portfolio context if requested
            portfolio_context = ""
            if include_portfolio and user_id:
                print(f"[DEBUG] Attempting to load portfolio for authenticated user {user_id}")
                from applications.portfolio_analyzer import PortfolioAnalyzer
                try:
                    analyzer = PortfolioAnalyzer(user_id)
                    analysis = analyzer.get_complete_analysis()
                    print(f"[DEBUG] Portfolio analysis retrieved for user {user_id}")
                    print(f"[DEBUG] Portfolio has {len(analysis['portfolio_data']['holdings'])} holdings")
                    
                    # Build portfolio summary for AI
                    portfolio_summary = f"""
User's Current Portfolio:
- Total Portfolio Value: ₹{analysis['portfolio_data']['total_value']:.2f}
- Total Invested: ₹{analysis['portfolio_data']['total_invested']:.2f}
- Portfolio Health Score: {analysis['health_score']['score']}/10 ({analysis['health_score']['rating']})
- Risk Level: {analysis['risk_assessment']['risk_level']}
- Diversification Score: {analysis['diversification']['diversification_score']}/10
- Top Holding: {analysis['diversification']['holdings_breakdown'][0]['symbol'] if analysis['diversification']['holdings_breakdown'] else 'N/A'} ({analysis['diversification']['holdings_breakdown'][0]['percentage'] if analysis['diversification']['holdings_breakdown'] else 0}% of portfolio)
- Performance: {analysis['performance']['gain_loss_percent']:.2f}% ({'+' if analysis['performance']['gain_loss'] >= 0 else ''}₹{analysis['performance']['total_gain_loss']:.2f})

Holdings:
"""
                    for holding in analysis['portfolio_data']['holdings']:
                        portfolio_summary += f"- {holding['symbol']}: {holding['quantity']} shares, Gain/Loss: {holding['gain_loss_percent']:.2f}%\n"
                    
                    portfolio_context = portfolio_summary
                    print(f"[DEBUG] Portfolio context prepared: {len(portfolio_context)} characters")
                except Exception as e:
                    print(f"[ERROR] Error loading portfolio: {e}")
                    import traceback
                    traceback.print_exc()
                    portfolio_context = ""

            # Create financial advisor prompt
            system_prompt = """You are a friendly and knowledgeable financial advisor for retail investors.
Provide clear, helpful advice about stocks, investing, portfolios, and financial planning.
Keep responses concise but informative. Use simple language for complex concepts.
If the user has shared their portfolio, provide personalized advice based on their holdings and risk profile."""

            if portfolio_context:
                full_prompt = f"{system_prompt}\n\n{portfolio_context}\n\nUser: {message}"
                print(f"[DEBUG] Portfolio context INCLUDED in AI prompt")
            else:
                full_prompt = f"{system_prompt}\n\nUser: {message}"
                print(f"[DEBUG] No portfolio context included")

            # Get AI response
            response = model.generate_content(full_prompt)
            ai_response = response.text

            return make_response(jsonify({
                'message': message,
                'response': ai_response,
                'portfolio_context_included': bool(portfolio_context),
                'user_id': user_id
            }), 200)

        except Exception as e:
            error_msg = str(e)
            print(f"[AI_CHAT_ERROR] {error_msg}")
            
            # Provide user-friendly error messages
            if "API key" in error_msg or "invalid" in error_msg.lower():
                return make_response(jsonify({'message': 'Chat service temporarily unavailable. Please try again later.'}), 503)
            else:
                return make_response(jsonify({'message': f'Chat failed: {error_msg}'}), 500)

