#!/usr/bin/env python3
"""
Railway startup script for Machinecraft Inventory Slack Bot
Handles PORT environment variable and proper startup
"""

import os
import sys
from deploy_slack_bot import app, bot

def main():
    """Main startup function for Railway"""
    print("🚀 Starting Machinecraft Inventory Slack Bot on Railway...")
    
    # Check required environment variables
    if not os.environ.get("SLACK_BOT_TOKEN"):
        print("❌ Error: SLACK_BOT_TOKEN environment variable not set")
        sys.exit(1)
    
    # Get port from Railway environment
    port = int(os.environ.get("PORT", 5000))
    
    print(f"📊 Database: {bot.db_path}")
    print(f"🔑 Bot token: {'Set' if bot.slack_token else 'Not set'}")
    print(f"🔐 Signing secret: {'Set' if bot.signing_secret else 'Not set'}")
    print(f"🌐 Port: {port}")
    
    # Test database connection
    try:
        conn = bot.connect_db()
        cursor = conn.execute("SELECT COUNT(*) FROM silver_inventory_items")
        count = cursor.fetchone()[0]
        conn.close()
        print(f"✅ Database connected: {count:,} items available")
    except Exception as e:
        print(f"⚠️  Database warning: {str(e)}")
        print("🔄 Creating fallback database...")
        # The bot will create a minimal database automatically
    
    # Start the Flask app
    print(f"🚀 Starting server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == '__main__':
    main()
