#!/usr/bin/env python3
"""
Test script for Portfolio API endpoints
Tests: CRUD operations, analysis, goals tracking
"""
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:5001/api/v1"
USER_ID = 1

def test_portfolio_endpoints():
    """Test all portfolio endpoints"""
    
    print("\n" + "="*60)
    print("🧪 PORTFOLIO API TEST SUITE")
    print("="*60)
    
    # Test 1: Add first stock to portfolio
    print("\n[TEST 1] Adding stock to portfolio (TCS)...")
    response = requests.post(
        f"{BASE_URL}/portfolio/holdings/{USER_ID}",
        json={
            "symbol": "TCS",
            "quantity": 10,
            "purchase_price": 3500
        }
    )
    print(f"Status: {response.status_code}")
    if response.status_code in [200, 201]:
        print("✅ Stock added successfully")
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"❌ Error: {response.text}")
    
    # Test 2: Add second stock
    print("\n[TEST 2] Adding second stock to portfolio (RELIANCE)...")
    response = requests.post(
        f"{BASE_URL}/portfolio/holdings/{USER_ID}",
        json={
            "symbol": "RELIANCE",
            "quantity": 5,
            "purchase_price": 2800
        }
    )
    print(f"Status: {response.status_code}")
    if response.status_code in [200, 201]:
        print("✅ Stock added successfully")
    else:
        print(f"❌ Error: {response.text}")
    
    # Test 3: Get all holdings
    print("\n[TEST 3] Getting all holdings...")
    response = requests.get(f"{BASE_URL}/portfolio/holdings/{USER_ID}")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Retrieved {len(data.get('holdings', []))} holdings")
        print(json.dumps(data, indent=2))
    else:
        print(f"❌ Error: {response.text}")
    
    # Test 4: Get portfolio analysis
    print("\n[TEST 4] Getting portfolio analysis...")
    response = requests.get(f"{BASE_URL}/portfolio/analysis/{USER_ID}")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print("✅ Portfolio analysis retrieved")
        print(f"   Health Score: {data['health_score']['score']}/10 ({data['health_score']['rating']})")
        print(f"   Risk Level: {data['risk_assessment']['risk_level']}")
        print(f"   Diversification Score: {data['diversification']['diversification_score']}/10")
        print(f"   Total Value: ₹{data['portfolio_data']['total_value']:.2f}")
        print(f"   Performance: {data['performance']['gain_loss_percent']:.2f}%")
    else:
        print(f"❌ Error: {response.text}")
    
    # Test 5: Create investment goal
    print("\n[TEST 5] Creating investment goal...")
    target_date = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')
    response = requests.post(
        f"{BASE_URL}/portfolio/goals/{USER_ID}",
        json={
            "goal_name": "House Down Payment",
            "target_amount": 500000,
            "current_amount": 100000,
            "target_date": target_date,
            "description": "Save for house down payment"
        }
    )
    print(f"Status: {response.status_code}")
    if response.status_code in [200, 201]:
        data = response.json()
        print("✅ Goal created successfully")
        goal = data['goal']
        print(f"   Goal: {goal['goal_name']}")
        print(f"   Progress: {goal['progress_percent']:.1f}%")
        print(f"   Monthly needed: ₹{goal['monthly_contribution_needed']:.2f}")
    else:
        print(f"❌ Error: {response.text}")
    
    # Test 6: Get portfolio performance history
    print("\n[TEST 6] Getting portfolio performance history...")
    response = requests.get(f"{BASE_URL}/portfolio/performance/{USER_ID}?days=30")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Performance history retrieved ({len(data['history'])} snapshots)")
    else:
        print(f"❌ Error: {response.text}")
    
    # Test 7: AI Chat with portfolio context
    print("\n[TEST 7] Testing AI advisor with portfolio context...")
    response = requests.post(
        f"{BASE_URL}/ai/chat",
        json={
            "message": "Should I sell some TCS to rebalance my portfolio?",
            "user_id": USER_ID,
            "include_portfolio": True
        }
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print("✅ AI response received")
        print(f"   Portfolio context included: {data['portfolio_context_included']}")
        print(f"   Response preview: {data['response'][:200]}...")
    else:
        print(f"❌ Error: {response.text}")
    
    print("\n" + "="*60)
    print("✅ TEST SUITE COMPLETED")
    print("="*60 + "\n")


if __name__ == '__main__':
    print("Waiting 3 seconds for backend to start...")
    import time
    time.sleep(3)
    
    try:
        test_portfolio_endpoints()
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Could not connect to backend at http://localhost:5001")
        print("Make sure Flask server is running!")
    except Exception as e:
        print(f"❌ ERROR: {e}")
