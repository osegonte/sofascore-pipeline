"""
Basic tests to verify setup is working correctly
"""

import requests
import pandas as pd
import sys
import os

def test_imports():
    """Test that required libraries can be imported"""
    try:
        import requests
        import pandas as pd
        print("✅ All required libraries imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_internet_connection():
    """Test internet connectivity"""
    try:
        response = requests.get("https://api.sofascore.com", timeout=10)
        print("✅ Internet connection and SofaScore API accessible")
        return True
    except requests.RequestException as e:
        print(f"❌ Connection error: {e}")
        return False

def run_tests():
    """Run all setup tests"""
    print("Running setup verification tests...")
    print("-" * 35)
    
    tests_passed = 0
    total_tests = 2
    
    if test_imports():
        tests_passed += 1
    
    if test_internet_connection():
        tests_passed += 1
    
    print("-" * 35)
    print(f"Tests passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("🎉 Setup verification completed successfully!")
    else:
        print("⚠️  Some tests failed. Check the output above.")

if __name__ == "__main__":
    run_tests()
