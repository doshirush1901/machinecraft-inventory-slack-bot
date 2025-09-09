#!/usr/bin/env python3
"""
Test script for Railway deployment
"""

import os
import sys

def test_environment():
    """Test environment variables and dependencies"""
    print("🧪 Testing Railway Environment...")
    
    # Check Python version
    print(f"🐍 Python version: {sys.version}")
    
    # Check environment variables
    slack_token = os.environ.get("SLACK_BOT_TOKEN")
    signing_secret = os.environ.get("SLACK_SIGNING_SECRET")
    port = os.environ.get("PORT", "5000")
    
    print(f"🔑 SLACK_BOT_TOKEN: {'Set' if slack_token else 'Not set'}")
    print(f"🔐 SLACK_SIGNING_SECRET: {'Set' if signing_secret else 'Not set'}")
    print(f"🌐 PORT: {port}")
    
    # Test imports
    try:
        import flask
        print(f"✅ Flask: {flask.__version__}")
    except ImportError as e:
        print(f"❌ Flask import error: {e}")
        return False
    
    try:
        import pandas
        print(f"✅ Pandas: {pandas.__version__}")
    except ImportError as e:
        print(f"❌ Pandas import error: {e}")
        return False
    
    try:
        from slack_sdk import WebClient
        print("✅ Slack SDK: Available")
    except ImportError as e:
        print(f"❌ Slack SDK import error: {e}")
        return False
    
    # Test database
    try:
        import sqlite3
        conn = sqlite3.connect("machinecraft_inventory_pipeline.db")
        cursor = conn.execute("SELECT COUNT(*) FROM silver_inventory_items")
        count = cursor.fetchone()[0]
        conn.close()
        print(f"✅ Database: {count:,} items available")
    except Exception as e:
        print(f"⚠️  Database: {e}")
        print("🔄 Will create fallback database...")
    
    print("🎉 Environment test completed!")
    return True

if __name__ == "__main__":
    test_environment()
