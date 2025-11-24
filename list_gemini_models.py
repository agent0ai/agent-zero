#!/usr/bin/env python3
"""
List all available Gemini models
"""

import google.generativeai as genai

# Configure API key
api_key = "AIzaSyA8QWnuYKEhPUw8mN6YxCsTm6e01yXn78E"
genai.configure(api_key=api_key)

print("Available Gemini Models:")
print("="*50)

for model in genai.list_models():
    if 'generateContent' in model.supported_generation_methods:
        print(f"Model: {model.name}")
        print(f"  Display name: {model.display_name}")
        print(f"  Supported methods: {', '.join(model.supported_generation_methods)}")
        print()