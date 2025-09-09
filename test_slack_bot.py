#!/usr/bin/env python3
"""
Test script for Machinecraft Inventory Slack Bot
Demonstrates the bot's search capabilities
"""

import os
from slack_inventory_bot import SlackInventoryBot

def test_bot_functionality():
    """Test the bot's search functionality"""
    print("🤖 Testing Machinecraft Inventory Slack Bot...")
    
    # Initialize bot
    bot = SlackInventoryBot()
    
    # Test searches
    test_queries = [
        "servo motors",
        "expensive items", 
        "mitsubishi",
        "out of stock",
        "pneumatic components",
        "electrical components"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Testing: '{query}'")
        print("=" * 50)
        
        try:
            results = bot.natural_language_search(query)
            print(results['text'])
            
            # Show first few attachments
            for i, attachment in enumerate(results['attachments'][:3]):
                print(f"\n📦 Item {i+1}:")
                for field in attachment['fields']:
                    print(f"  {field['title']}: {field['value']}")
            
            if len(results['attachments']) > 3:
                print(f"\n... and {len(results['attachments']) - 3} more items")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    # Test inventory summary
    print(f"\n📊 Inventory Summary:")
    print("=" * 50)
    try:
        summary = bot.get_inventory_summary()
        print(summary)
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_bot_functionality()
