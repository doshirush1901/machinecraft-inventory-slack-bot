#!/usr/bin/env python3
"""
Simple health check for Railway
"""

import os
import sys
import json
from datetime import datetime

def health_check():
    """Simple health check"""
    try:
        # Test basic functionality
        port = os.environ.get("PORT", "5000")
        slack_token = os.environ.get("SLACK_BOT_TOKEN")
        signing_secret = os.environ.get("SLACK_SIGNING_SECRET")
        
        # Test database
        try:
            import sqlite3
            conn = sqlite3.connect("machinecraft_inventory_pipeline.db")
            cursor = conn.execute("SELECT COUNT(*) FROM silver_inventory_items")
            count = cursor.fetchone()[0]
            conn.close()
            database_status = "connected"
            items_count = count
        except Exception as e:
            database_status = "fallback"
            items_count = 1
        
        response = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": database_status,
            "items_count": items_count,
            "bot_token_set": bool(slack_token),
            "signing_secret_set": bool(signing_secret),
            "port": port
        }
        
        print("Content-Type: application/json")
        print("Status: 200 OK")
        print()
        print(json.dumps(response, indent=2))
        
    except Exception as e:
        error_response = {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }
        
        print("Content-Type: application/json")
        print("Status: 500 Internal Server Error")
        print()
        print(json.dumps(error_response, indent=2))
        sys.exit(1)

if __name__ == "__main__":
    health_check()
