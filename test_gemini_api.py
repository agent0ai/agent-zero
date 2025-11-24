#!/usr/bin/env python3
"""
Direct test of Gemini API to verify it's working
"""

import os
import google.generativeai as genai

# Configure API key
api_key = "AIzaSyA8QWnuYKEhPUw8mN6YxCsTm6e01yXn78E"
genai.configure(api_key=api_key)

print("Testing Gemini API directly...")
print(f"API Key: {api_key[:20]}...")

try:
    # Test gemini-2.5-pro
    print("\nTesting gemini-2.5-pro...")
    model = genai.GenerativeModel('gemini-2.5-pro')
    response = model.generate_content("Say 'Test successful' if you receive this.")
    print(f"Response: {response.text}")

    # Test gemini-2.5-flash
    print("\nTesting gemini-2.5-flash...")
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content("Say 'Flash model working' if you receive this.")
    print(f"Response: {response.text}")

    print("\n[SUCCESS] Gemini API is working correctly!")

except Exception as e:
    print(f"\n[ERROR] Failed to connect to Gemini API: {str(e)}")
    print("\nCommon issues:")
    print("1. API key may be invalid or expired")
    print("2. Network connectivity issues")
    print("3. API quota exceeded")