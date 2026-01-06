#!/usr/bin/env python3
"""
Debug script to test the import issue in Docker environment
"""

import sys
import os

print("=== DEBUGGING IMPORT ISSUE ===")
print(f"Current working directory: {os.getcwd()}")
print(f"Python path: {sys.path}")
print(f"Python version: {sys.version}")

# Check if bot_logic directory exists
bot_logic_path = "/app/bot_logic"
print(f"\nChecking if {bot_logic_path} exists: {os.path.exists(bot_logic_path)}")

if os.path.exists(bot_logic_path):
    print(f"Contents of {bot_logic_path}:")
    for item in os.listdir(bot_logic_path):
        print(f"  - {item}")
    
    # Check if prompt_templates.py exists
    prompt_templates_path = os.path.join(bot_logic_path, "prompt_templates.py")
    print(f"\nChecking if {prompt_templates_path} exists: {os.path.exists(prompt_templates_path)}")
    
    # Check if __init__.py exists
    init_path = os.path.join(bot_logic_path, "__init__.py")
    print(f"Checking if {init_path} exists: {os.path.exists(init_path)}")

# Try to import
print("\n=== ATTEMPTING IMPORTS ===")

# Test 1: Direct import
try:
    from bot_logic.prompt_templates import get_current_prompt_template, update_prompt_template
    print("✅ SUCCESS: Direct import worked!")
    template = get_current_prompt_template()
    print(f"Template length: {len(template)} characters")
except ImportError as e:
    print(f"❌ FAILED: Direct import failed: {e}")

# Test 2: Check if bot_logic is recognized as a package
try:
    import bot_logic
    print("✅ SUCCESS: bot_logic package imported")
    print(f"bot_logic module: {bot_logic}")
    print(f"bot_logic.__file__: {getattr(bot_logic, '__file__', 'No __file__ attribute')}")
except ImportError as e:
    print(f"❌ FAILED: bot_logic package import failed: {e}")

# Test 3: Try importing individual modules
try:
    import bot_logic.strategy
    print("✅ SUCCESS: bot_logic.strategy imported")
except ImportError as e:
    print(f"❌ FAILED: bot_logic.strategy import failed: {e}")

# Test 4: Check sys.modules
print(f"\n=== PYTHON MODULES ===")
print("bot_logic in sys.modules:", "bot_logic" in sys.modules)
if "bot_logic" in sys.modules:
    print(f"bot_logic module: {sys.modules['bot_logic']}")

print("\n=== FILE SYSTEM CHECK ===")
# Check if we can read the file directly
try:
    with open("/app/bot_logic/prompt_templates.py", "r") as f:
        content = f.read(100)  # Read first 100 chars
        print(f"✅ SUCCESS: Can read file directly. First 100 chars: {content[:100]}...")
except Exception as e:
    print(f"❌ FAILED: Cannot read file directly: {e}")

print("\n=== DEBUG COMPLETE ===")