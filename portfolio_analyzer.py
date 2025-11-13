"""
Portfolio Analysis Engine
Calculates portfolio health, risk assessment, diversification, and performance metrics
"""
import yfinance as yf
from applications.models import PortfolioHolding, PortfolioSnapshot
from applications.database import db
import datetime


class PortfolioAnalyzer:
    """
    Analyzes user portfolios and generates metrics for AI recommendations
    """
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.holdings = PortfolioHolding.query.filter_by(user_id=user_id).all()
    
    def get_portfolio_data(self):
        """Get all portfolio holdings as a dictionary"""
        return {
            'holdings': [h.to_dict() for h in self.holdings],
            'total_value': self._calculate_total_value(),
            'total_invested': self._calculate_total_invested(),
        }
    
    def _calculate_total_value(self):
        """Calculate total current portfolio value"""
        return sum(h.current_value for h in self.holdings) if self.holdings else 0
    
    def _calculate_total_invested(self):
        """Calculate total amount invested"""
        return sum(h.quantity * h.purchase_price for h in self.holdings) if self.holdings else 0
    
    def health_score(self):
        """
        Calculate portfolio health score (1-10)
        Factors: Diversification, gains/losses, number of holdings
        """
        if not self.holdings:
            return {
                'score': 0,
                'rating': 'No Portfolio',
                'explanation': 'No holdings found. Start by adding stocks to your portfolio.'
            }
        
        score = 5  # Base score
        
        # Factor 1: Number of holdings (more is better for diversification)
        num_holdings = len(self.holdings)
        if num_holdings >= 5:
            score += 2
        elif num_holdings >= 3:
            score += 1
        else:
            score -= 1
        
        # Factor 2: Diversification (concentration check)
        total_value = self._calculate_total_value()
        if total_value > 0:
            max_holding_pct = max(h.current_value / total_value * 100 for h in self.holdings)
            if max_holding_pct <= 30:
                score += 2
            elif max_holding_pct <= 50:
                score += 1
            else:
                score -= 1
        
        # Factor 3: Overall gains/losses
        total_invested = self._calculate_total_invested()
        if total_invested > 0:
            total_gain = total_value - total_invested
            gain_pct = (total_gain / total_invested) * 100
            if gain_pct > 20:
                score += 2
            elif gain_pct > 0:
                score += 1
            elif gain_pct < -20:
                score -= 2
            else:
                score -= 1
        
        # Clamp score to 1-10
        score = max(1, min(10, score))
        
        # Determine rating
        if score >= 8:
            rating = 'Excellent'
        elif score >= 6:
            rating = 'Good'
        elif score >= 4:
            rating = 'Fair'
        else:
            rating = 'Needs Attention'
        
        return {
            'score': score,
            'rating': rating,
            'num_holdings': num_holdings,
            'max_holding_percent': round(max(h.current_value / total_value * 100 for h in self.holdings) if total_value > 0 else 0, 2),
        }
    
    def diversification_analysis(self):
        """
        Analyze portfolio diversification across sectors and individual stocks
        """
        if not self.holdings:
            return {
                'message': 'No holdings to analyze',
                'diversification_score': 0,
                'holdings_breakdown': []
            }
        
        total_value = self._calculate_total_value()
        holdings_breakdown = []
        
        for holding in self.holdings:
            pct_of_portfolio = round((holding.current_value / total_value * 100), 2) if total_value > 0 else 0
            holdings_breakdown.append({
                'symbol': holding.symbol,
                'value': round(holding.current_value, 2),
                'percentage': pct_of_portfolio,
                'quantity': holding.quantity
            })
        
        # Sort by value
        holdings_breakdown.sort(key=lambda x: x['value'], reverse=True)
        
        # Calculate diversification score (lower concentration = higher score)
        if holdings_breakdown:
            max_pct = holdings_breakdown[0]['percentage']
            if max_pct <= 20:
                diversification_score = 9
            elif max_pct <= 35:
                diversification_score = 7
            elif max_pct <= 50:
                diversification_score = 5
            else:
                diversification_score = 3
        else:
            diversification_score = 0
        
        return {
            'diversification_score': diversification_score,
            'holdings_breakdown': holdings_breakdown,
            'top_holding_percent': holdings_breakdown[0]['percentage'] if holdings_breakdown else 0,
            'recommendation': 'Try to keep top holding below 30% for better diversification' if holdings_breakdown and holdings_breakdown[0]['percentage'] > 30 else 'Good diversification'
        }
    
    def risk_assessment(self):
        """
        Assess portfolio risk based on concentration and volatility
        """
        if not self.holdings:
            return {
                'risk_level': 'No Data',
                'risk_score': 0,
                'explanation': 'No holdings to assess'
            }
        
        total_value = self._calculate_total_value()
        concentration_risk = 0
        
        # Check concentration
        if total_value > 0:
            max_holding_pct = max(h.current_value / total_value * 100 for h in self.holdings)
            if max_holding_pct > 50:
                concentration_risk = 3  # High
            elif max_holding_pct > 30:
                concentration_risk = 2  # Medium
            else:
                concentration_risk = 1  # Low
        
        # Overall risk score (1-10)
        risk_score = concentration_risk + (len(self.holdings) - 5)  # Fewer holdings = more risk
        risk_score = max(1, min(10, risk_score))
        
        if risk_score >= 7:
            risk_level = 'High Risk'
        elif risk_score >= 4:
            risk_level = 'Moderate Risk'
        else:
            risk_level = 'Low Risk'
        
        return {
            'risk_level': risk_level,
            'risk_score': risk_score,
            'concentration_risk': concentration_risk,
            'explanation': f'Your portfolio has {concentration_risk} concentration risk level',
            'recommendation': 'Consider adding more stocks for diversification' if len(self.holdings) < 3 else 'Good portfolio spread'
        }
    
    def performance_analysis(self):
        """
        Calculate overall portfolio performance
        """
        if not self.holdings:
            return {
                'total_value': 0,
                'total_invested': 0,
                'total_gain_loss': 0,
                'gain_loss_percent': 0,
                'message': 'No holdings to analyze'
            }
        
        total_value = self._calculate_total_value()
        total_invested = self._calculate_total_invested()
        total_gain_loss = total_value - total_invested
        gain_loss_percent = round((total_gain_loss / total_invested * 100), 2) if total_invested > 0 else 0
        
        # Get best and worst performers
        sorted_holdings = sorted(self.holdings, key=lambda h: h.to_dict()['gain_loss_percent'], reverse=True)
        
        best_performer = sorted_holdings[0].to_dict() if sorted_holdings else None
        worst_performer = sorted_holdings[-1].to_dict() if sorted_holdings else None
        
        return {
            'total_value': round(total_value, 2),
            'total_invested': round(total_invested, 2),
            'total_gain_loss': round(total_gain_loss, 2),
            'gain_loss_percent': gain_loss_percent,
            'best_performer': {
                'symbol': best_performer['symbol'],
                'gain_loss_percent': best_performer['gain_loss_percent']
            } if best_performer else None,
            'worst_performer': {
                'symbol': worst_performer['symbol'],
                'gain_loss_percent': worst_performer['gain_loss_percent']
            } if worst_performer else None,
        }
    
    def get_complete_analysis(self):
        """
        Generate complete portfolio analysis
        """
        return {
            'user_id': self.user_id,
            'timestamp': datetime.datetime.utcnow().isoformat(),
            'portfolio_data': self.get_portfolio_data(),
            'health_score': self.health_score(),
            'diversification': self.diversification_analysis(),
            'risk_assessment': self.risk_assessment(),
            'performance': self.performance_analysis(),
        }
    
    def save_snapshot(self):
        """
        Save current portfolio value as a historical snapshot
        """
        try:
            total_value = self._calculate_total_value()
            snapshot = PortfolioSnapshot(
                user_id=self.user_id,
                total_value=total_value,
                snapshot_date=datetime.datetime.utcnow()
            )
            db.session.add(snapshot)
            db.session.commit()
            return True
        except Exception as e:
            print(f"Error saving snapshot: {e}")
            db.session.rollback()
            return False
    
    def get_performance_history(self, days=30):
        """
        Get historical performance data for charting
        """
        try:
            cutoff_date = datetime.datetime.utcnow() - datetime.timedelta(days=days)
            snapshots = PortfolioSnapshot.query.filter(
                PortfolioSnapshot.user_id == self.user_id,
                PortfolioSnapshot.snapshot_date >= cutoff_date
            ).order_by(PortfolioSnapshot.snapshot_date.asc()).all()
            
            if not snapshots:
                return []
            
            return [s.to_dict() for s in snapshots]
        except Exception as e:
            print(f"Error retrieving history: {e}")
            return []
