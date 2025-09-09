#!/bin/bash
# Machinecraft Inventory Slack Bot Startup Script

echo "🚀 Starting Machinecraft Inventory Slack Bot..."

# Check if environment variables are set
if [ -z "$SLACK_BOT_TOKEN" ]; then
    echo "❌ Error: SLACK_BOT_TOKEN environment variable not set"
    echo "Please set it with: export SLACK_BOT_TOKEN='your-token-here'"
    exit 1
fi

if [ -z "$SLACK_SIGNING_SECRET" ]; then
    echo "⚠️  Warning: SLACK_SIGNING_SECRET not set. Bot will run without signature verification."
fi

# Check if database exists
if [ ! -f "machinecraft_inventory_pipeline.db" ]; then
    echo "❌ Error: Database file not found!"
    echo "Please ensure machinecraft_inventory_pipeline.db is in the current directory"
    exit 1
fi

# Check if Python dependencies are installed
echo "🔍 Checking dependencies..."
python3 -c "import slack_sdk, pandas, flask" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📦 Installing dependencies..."
    pip3 install -r requirements_slack.txt
    pip3 install flask gunicorn
fi

# Test database connection
echo "🗄️  Testing database connection..."
python3 -c "
import sqlite3
try:
    conn = sqlite3.connect('machinecraft_inventory_pipeline.db')
    cursor = conn.execute('SELECT COUNT(*) FROM silver_inventory_items')
    count = cursor.fetchone()[0]
    conn.close()
    print(f'✅ Database connected: {count:,} items available')
except Exception as e:
    print(f'❌ Database error: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    exit 1
fi

# Test Slack API connection
echo "🔗 Testing Slack API connection..."
python3 -c "
import os
from slack_sdk import WebClient
try:
    client = WebClient(token=os.environ.get('SLACK_BOT_TOKEN'))
    response = client.auth_test()
    print(f'✅ Slack API connected: {response[\"user\"]} in {response[\"team\"]}')
except Exception as e:
    print(f'❌ Slack API error: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    exit 1
fi

echo ""
echo "🎉 All checks passed! Starting bot..."
echo "📊 Bot will be available at: http://localhost:5000"
echo "🔍 Health check: http://localhost:5000/health"
echo "🧪 Test endpoint: http://localhost:5000/test"
echo ""
echo "💬 Usage in Slack:"
echo "  - 'inventory servo motors'"
echo "  - 'inventory expensive items'"
echo "  - 'inventory mitsubishi'"
echo "  - 'inventory summary'"
echo ""
echo "Press Ctrl+C to stop the bot"
echo ""

# Start the bot
python3 deploy_slack_bot.py
