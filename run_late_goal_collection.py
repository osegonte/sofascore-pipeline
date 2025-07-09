#!/usr/bin/env python3
"""
Late Goal Prediction Launcher
Main entry point for all late goal prediction functionality
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def show_menu():
    """Show main menu"""
    print("\n🎯 Late Goal Prediction System")
    print("=" * 40)
    print("1. 🧪 Quick System Test")
    print("2. 📊 Simple Data Collection")
    print("3. 🔄 Continuous Monitoring")
    print("4. 📈 View Dashboard")
    print("5. 🔍 Data Verification")
    print("0. 🚪 Exit")
    print()

def quick_test():
    """Run quick system test"""
    print("\n🚀 Running Quick System Test...")
    try:
        exec(open('quick_test.py').read())
    except Exception as e:
        print(f"❌ Error running quick test: {e}")

def simple_collection():
    """Run simple data collection"""
    print("\n📊 Running Simple Data Collection...")
    try:
        sys.path.insert(0, os.path.join(project_root, 'src'))
        from late_goal.data_collector import SimpleDataCollector
        
        collector = SimpleDataCollector()
        collector.main()
    except Exception as e:
        print(f"❌ Error running simple collection: {e}")
        print("Make sure you've created src/late_goal/data_collector.py")

def continuous_monitoring():
    """Run continuous monitoring"""
    print("\n🔄 Starting Continuous Monitoring...")
    print("Press Ctrl+C to stop")
    try:
        sys.path.insert(0, os.path.join(project_root, 'src'))
        from late_goal.continuous_monitor import ContinuousMonitor
        
        monitor = ContinuousMonitor()
        monitor.start_monitoring()
    except KeyboardInterrupt:
        print("\n⏹️  Monitoring stopped by user")
    except Exception as e:
        print(f"❌ Error running continuous monitoring: {e}")

def view_dashboard():
    """View monitoring dashboard"""
    print("\n📈 Opening Dashboard...")
    try:
        sys.path.insert(0, os.path.join(project_root, 'src'))
        from late_goal.dashboard import MonitoringDashboard
        
        dashboard = MonitoringDashboard()
        dashboard.run()
    except Exception as e:
        print(f"❌ Error running dashboard: {e}")

def data_verification():
    """Run data verification"""
    print("\n🔍 Running Data Verification...")
    try:
        sys.path.insert(0, os.path.join(project_root, 'src'))
        from late_goal.data_verifier import DataVerifier
        
        verifier = DataVerifier()
        print("Data verification functionality coming soon...")
    except Exception as e:
        print(f"❌ Error running data verification: {e}")

def main():
    """Main launcher function"""
    print("🎯 Welcome to Late Goal Prediction System!")
    
    while True:
        show_menu()
        choice = input("Select option (0-5): ").strip()
        
        if choice == '0':
            print("👋 Goodbye!")
            break
        elif choice == '1':
            quick_test()
        elif choice == '2':
            simple_collection()
        elif choice == '3':
            continuous_monitoring()
        elif choice == '4':
            view_dashboard()
        elif choice == '5':
            data_verification()
        else:
            print("❌ Invalid choice. Please select 0-5.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()