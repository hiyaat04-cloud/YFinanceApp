#!/usr/bin/env python3
"""
Setup Gemini API Key
Get your free API key from: https://aistudio.google.com/app/apikey
"""

import os
from pathlib import Path

def setup_api_key():
    """Setup or update Gemini API key"""
    print("\n" + "="*60)
    print("🔑 GEMINI API KEY SETUP")
    print("="*60)
    
    print("\n📌 IMPORTANT: Get your FREE API key:")
    print("   1. Go to: https://aistudio.google.com/app/apikey")
    print("   2. Click 'Create API key'")
    print("   3. Copy the key")
    print("   4. Paste it below")
    
    api_key = input("\n🔐 Enter your Gemini API Key: ").strip()
    
    if not api_key or api_key.startswith("AIzaSyD"):  # Check if it's still placeholder
        print("❌ Invalid API key. Please use your actual key.")
        return False
    
    # Update .env file
    env_path = Path(__file__).parent / '.env'
    
    with open(env_path, 'r') as f:
        lines = f.readlines()
    
    # Replace API key line
    with open(env_path, 'w') as f:
        for line in lines:
            if line.startswith('GEMINI_API_KEY='):
                f.write(f'GEMINI_API_KEY={api_key}\n')
            else:
                f.write(line)
    
    print(f"\n✅ API key saved to {env_path}")
    print("✅ You can now use AI features!")
    return True

if __name__ == '__main__':
    setup_api_key()
