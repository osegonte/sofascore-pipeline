#!/usr/bin/env python3
"""
Essential test runner for production validation
Minimal testing for core functionality
"""

import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_database():
    """Test database connectivity"""
    try:
        from config.database import test_connection
        return test_connection()
    except Exception:
        return False

def test_data_quality():
    """Test basic data quality"""
    try:
        from config.database import engine
        from sqlalchemy import text
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM live_matches"))
            matches = result.scalar()
            result = conn.execute(text("SELECT COUNT(*) FROM goal_events"))
            goals = result.scalar()
            return matches > 0 or goals > 0
    except Exception:
        return False

def main():
    """Run essential tests"""
    print("SofaScore Pipeline - Essential Tests")
    print("=" * 40)
    
    tests = [
        ("Database Connection", test_database),
        ("Data Quality", test_data_quality)
    ]
    
    passed = 0
    for test_name, test_func in tests:
        try:
            result = test_func()
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name}: {status}")
            if result:
                passed += 1
        except Exception as e:
            print(f"{test_name}: ❌ ERROR - {e}")
    
    print(f"\nResults: {passed}/{len(tests)} tests passed")
    return 0 if passed == len(tests) else 1

if __name__ == "__main__":
    sys.exit(main())
