#!/usr/bin/env python3
"""
Late Goal Prediction Setup Script
Comprehensive setup and testing for the late goal prediction system
"""

import os
import sys
import subprocess
import time
from datetime import datetime
import pandas as pd
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class LateGoalSetup:
    """Setup manager for late goal prediction system"""
    
    def __init__(self):
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.setup_complete = False
        
    def check_dependencies(self):
        """Check if all required dependencies are installed"""
        print("🔍 Checking dependencies...")
        
        required_packages = [
            'pandas', 'requests', 'sqlalchemy', 'psycopg2-binary', 'schedule'
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                print(f"   ✅ {package}")
            except ImportError:
                missing_packages.append(package)
                print(f"   ❌ {package} - Missing")
        
        if missing_packages:
            print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
            print("Run: pip install " + " ".join(missing_packages))
            return False
        
        return True
    
    def check_database_connection(self):
        """Check database connection"""
        print("\n🔍 Checking database connection...")
        
        try:
            from config.database import test_connection
            if test_connection():
                print("   ✅ Database connection successful")
                return True
            else:
                print("   ❌ Database connection failed")
                return False
        except Exception as e:
            print(f"   ❌ Database connection error: {e}")
            return False
    
    def create_directories(self):
        """Create necessary directories"""
        print("\n📁 Creating directories...")
        
        directories = [
            'exports',
            'logs',
            'tests/reports',
            'exports/backups'
        ]
        
        for directory in directories:
            full_path = os.path.join(self.project_root, directory)
            if not os.path.exists(full_path):
                os.makedirs(full_path)
                print(f"   ✅ Created: {directory}")
            else:
                print(f"   ℹ️  Already exists: {directory}")
    
    def test_api_connectivity(self):
        """Test SofaScore API connectivity"""
        print("\n🌐 Testing API connectivity...")
        
        try:
            from src.utils import make_api_request
            
            # Test with live matches endpoint
            url = "https://api.sofascore.com/api/v1/sport/football/events/live"
            response = make_api_request(url)
            
            if response:
                matches = response.get('events', [])
                print(f"   ✅ API accessible - {len(matches)} live matches found")
                return True
            else:
                print("   ❌ API not accessible")
                return False
                
        except Exception as e:
            print(f"   ❌ API test error: {e}")
            return False
    
    def run_sample_collection(self):
        """Run a sample data collection"""
        print("\n📊 Running sample data collection...")
        
        try:
            from src.live_scraper import LiveMatchScraper
            
            scraper = LiveMatchScraper()
            
            # Get live matches
            live_matches = scraper.get_live_matches()
            
            if not live_matches:
                print("   ⚠️  No live matches found (this is normal if no matches are currently live)")
                return True
            
            print(f"   ✅ Found {len(live_matches)} live matches")
            
            # Test detailed data collection on first match
            if live_matches:
                match_id = live_matches[0].get('match_id')
                if match_id:
                    details = scraper.get_match_comprehensive_details(match_id)
                    if details:
                        print(f"   ✅ Successfully collected detailed data for match {match_id}")
                    else:
                        print(f"   ⚠️  Could not collect detailed data for match {match_id}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Sample collection error: {e}")
            return False
    
    def setup_database_tables(self):
        """Set up database tables if needed"""
        print("\n🗄️  Setting up database tables...")
        
        try:
            schema_file = os.path.join(self.project_root, 'database', 'schema.sql')
            
            if os.path.exists(schema_file):
                print("   ℹ️  Database schema file found")
                
                # Ask user if they want to run schema setup
                response = input("   Do you want to run database schema setup? (y/n): ").lower()
                
                if response == 'y':
                    from config.database import engine
                    from sqlalchemy import text
                    
                    with open(schema_file, 'r') as f:
                        schema_sql = f.read()
                    
                    with engine.connect() as conn:
                        conn.execute(text(schema_sql))
                        conn.commit()
                    
                    print("   ✅ Database schema setup completed")
                else:
                    print("   ⏭️  Skipping database schema setup")
            else:
                print("   ⚠️  Database schema file not found")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Database setup error: {e}")
            return False
    
    def run_full_setup(self):
        """Run complete setup process"""
        print("Late Goal Prediction System Setup")
        print("=" * 40)
        
        setup_steps = [
            ("Dependencies", self.check_dependencies),
            ("Directories", self.create_directories),
            ("Database", self.check_database_connection),
            ("API Connectivity", self.test_api_connectivity),
            ("Sample Collection", self.run_sample_collection),
            ("Database Tables", self.setup_database_tables)
        ]
        
        successful_steps = 0
        
        for step_name, step_function in setup_steps:
            print(f"\n{'='*50}")
            print(f"STEP: {step_name.upper()}")
            print(f"{'='*50}")
            
            try:
                if step_function():
                    successful_steps += 1
                    print(f"✅ {step_name} completed successfully")
                else:
                    print(f"❌ {step_name} failed")
                    
                    # Ask if user wants to continue
                    if step_name in ["Dependencies", "Database"]:
                        response = input(f"Continue setup without {step_name}? (y/n): ").lower()
                        if response != 'y':
                            print("Setup aborted.")
                            return False
                    
            except Exception as e:
                print(f"❌ {step_name} error: {e}")
        
        # Setup summary
        print(f"\n{'='*50}")
        print("SETUP SUMMARY")
        print(f"{'='*50}")
        
        print(f"Completed steps: {successful_steps}/{len(setup_steps)}")
        
        if successful_steps == len(setup_steps):
            print("🎉 Setup completed successfully!")
            self.setup_complete = True
            self.show_next_steps()
        else:
            print("⚠️  Setup completed with issues. Please review failed steps.")
            
        return self.setup_complete
    
    def show_next_steps(self):
        """Show next steps after setup"""
        print(f"\n🚀 NEXT STEPS:")
        print("=" * 20)
        
        print("1. 📊 Test Data Collection:")
        print("   python -c \"from late_goal_data_collector import LateGoalDataCollector; collector = LateGoalDataCollector(); collector.collect_live_matches_second_half()\"")
        
        print("\n2. 🔍 Verify Data Quality:")
        print("   python -c \"from data_verification_script import DataVerifier; verifier = DataVerifier()\"")
        
        print("\n3. 🔄 Start Continuous Monitoring:")
        print("   python continuous_monitoring_script.py")
        
        print("\n4. 📈 Monitor Results:")
        print("   - Check exports/ directory for CSV files")
        print("   - Review logs/ directory for execution logs")
        print("   - Monitor second-half matches only")
        
        print("\n5. 🎯 Model Development:")
        print("   - Once you have sufficient data (1-2 weeks)")
        print("   - Focus on matches with late goals (75+ minutes)")
        print("   - Use features like possession, shots, score difference")
        
        print(f"\n💡 TIPS:")
        print("   • Run during peak football hours for best results")
        print("   • Monitor major competitions (Premier League, Champions League)")
        print("   • Look for patterns in close matches (1-goal difference)")
        print("   • Consider team styles and historical late-goal tendencies")
    
    def create_quick_test_script(self):
        """Create a quick test script"""
        test_script = '''#!/usr/bin/env python3
"""
Quick test script for late goal prediction system
"""

import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def quick_test():
    """Run quick system test"""
    print("🚀 Quick System Test")
    print("=" * 30)
    
    # Test 1: Database connection
    try:
        from config.database import test_connection
        if test_connection():
            print("✅ Database: Connected")
        else:
            print("❌ Database: Failed")
    except Exception as e:
        print(f"❌ Database: Error - {e}")
    
    # Test 2: API connectivity
    try:
        from src.utils import make_api_request
        response = make_api_request("https://api.sofascore.com/api/v1/sport/football/events/live")
        if response:
            print(f"✅ API: Working - {len(response.get('events', []))} live matches")
        else:
            print("❌ API: No response")
    except Exception as e:
        print(f"❌ API: Error - {e}")
    
    # Test 3: Data collection
    try:
        from src.live_scraper import LiveMatchScraper
        scraper = LiveMatchScraper()
        matches = scraper.get_live_matches()
        print(f"✅ Collection: Working - {len(matches)} matches found")
    except Exception as e:
        print(f"❌ Collection: Error - {e}")
    
    print("\\n🎯 System test completed!")

if __name__ == "__main__":
    quick_test()
'''
        
        # Write test script to file
        test_file = os.path.join(self.project_root, 'quick_test.py')
        with open(test_file, 'w') as f:
            f.write(test_script)
        
        print(f"✅ Created quick test script: {test_file}")
        print("   Run with: python quick_test.py")

def main():
    """Main setup function"""
    setup = LateGoalSetup()
    
    print("Welcome to Late Goal Prediction System Setup!")
    print("=" * 50)
    print("This script will:")
    print("• Check dependencies and database connectivity")
    print("• Test API access to SofaScore")
    print("• Create necessary directories")
    print("• Run sample data collection")
    print("• Set up database tables if needed")
    print("• Provide next steps for data collection")
    
    response = input("\nProceed with setup? (y/n): ").lower()
    
    if response != 'y':
        print("Setup cancelled.")
        return
    
    # Run full setup
    success = setup.run_full_setup()
    
    if success:
        # Create quick test script
        setup.create_quick_test_script()
        
        print(f"\n🎉 SETUP COMPLETED SUCCESSFULLY!")
        print("Your late goal prediction system is ready!")
        
        # Show configuration summary
        print(f"\n📋 CONFIGURATION SUMMARY:")
        print(f"   • Focus: Second-half matches only (45+ minutes)")
        print(f"   • Collection interval: 5 minutes")
        print(f"   • Export interval: 15 minutes")
        print(f"   • Target: Late goals (75+ minutes)")
        print(f"   • Data format: CSV exports in exports/ directory")
        
        print(f"\n🚀 TO START DATA COLLECTION:")
        print("   1. python quick_test.py  # Test everything is working")
        print("   2. python continuous_monitoring_script.py  # Start monitoring")
        print("   3. Monitor exports/ directory for CSV files")
        
        print(f"\n💡 RECOMMENDED COLLECTION SCHEDULE:")
        print("   • Weekends: High activity (multiple leagues)")
        print("   • Weekdays: Champions League, Europa League")
        print("   • Peak hours: 12:00-22:00 UTC")
        print("   • Minimum collection: 1-2 weeks for initial model")
        
    else:
        print(f"\n⚠️  SETUP INCOMPLETE")
        print("Please review the errors above and fix them before proceeding.")
        print("You can run this setup script again after fixing issues.")

if __name__ == "__main__":
    main()