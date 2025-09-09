#!/usr/bin/env python3
"""
Slack Bot for Machinecraft Internal Inventory System
Natural language search through 10.5M+ inventory items
"""

import sqlite3
import pandas as pd
import requests
import json
import re
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import os
from datetime import datetime

class SlackInventoryBot:
    def __init__(self, db_path="machinecraft_inventory_pipeline.db"):
        self.db_path = db_path
        self.slack_token = os.environ.get("SLACK_BOT_TOKEN")
        self.client = WebClient(token=self.slack_token)
        
    def connect_db(self):
        """Connect to the inventory database"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def natural_language_search(self, query):
        """Convert natural language to SQL queries"""
        query_lower = query.lower()
        
        # Servo motor queries
        if any(word in query_lower for word in ['servo motor', 'servo', 'motor']):
            if 'mitsubishi' in query_lower:
                return self.search_servo_motors(brand='Mitsubishi')
            else:
                return self.search_servo_motors()
        
        # Pneumatic components
        elif any(word in query_lower for word in ['pneumatic', 'cylinder', 'valve', 'festo', 'smc']):
            return self.search_pneumatic_components()
        
        # Electrical components
        elif any(word in query_lower for word in ['electrical', 'contactor', 'mcb', 'mccb', 'eaton']):
            return self.search_electrical_components()
        
        # Cables and connectors
        elif any(word in query_lower for word in ['cable', 'wire', 'connector', 'lapp', 'phoenix']):
            return self.search_cables_connectors()
        
        # Price-based searches
        elif 'expensive' in query_lower or 'high price' in query_lower:
            return self.search_high_value_items()
        elif 'cheap' in query_lower or 'low price' in query_lower:
            return self.search_low_value_items()
        
        # Stock-based searches
        elif 'out of stock' in query_lower or 'no stock' in query_lower:
            return self.search_out_of_stock()
        elif 'in stock' in query_lower:
            return self.search_in_stock()
        
        # Brand searches
        elif 'mitsubishi' in query_lower:
            return self.search_by_brand('Mitsubishi')
        elif 'festo' in query_lower:
            return self.search_by_brand('FESTO')
        elif 'eaton' in query_lower:
            return self.search_by_brand('Eaton')
        
        # Default search
        else:
            return self.general_search(query)
    
    def search_servo_motors(self, brand=None):
        """Search for servo motors"""
        conn = self.connect_db()
        
        if brand:
            query = """
            SELECT part_number, description, brand, unit_price_inr, quantity, 
                   total_value_inr, stock_status, category
            FROM silver_inventory_items 
            WHERE brand = ? AND (description LIKE '%servo%' OR description LIKE '%motor%' 
                   OR part_number LIKE '%HG-%' OR part_number LIKE '%MR-%')
            ORDER BY unit_price_inr DESC
            LIMIT 10
            """
            df = pd.read_sql_query(query, conn, params=(brand,))
        else:
            query = """
            SELECT part_number, description, brand, unit_price_inr, quantity, 
                   total_value_inr, stock_status, category
            FROM silver_inventory_items 
            WHERE (description LIKE '%servo%' OR description LIKE '%motor%' 
                   OR part_number LIKE '%HG-%' OR part_number LIKE '%MR-%')
            ORDER BY unit_price_inr DESC
            LIMIT 10
            """
            df = pd.read_sql_query(query, conn)
        
        conn.close()
        return self.format_slack_results(df, "⚙️ Servo Motors")
    
    def search_pneumatic_components(self):
        """Search for pneumatic components"""
        conn = self.connect_db()
        query = """
        SELECT part_number, description, brand, unit_price_inr, quantity, 
               total_value_inr, stock_status, category
        FROM silver_inventory_items 
        WHERE category = 'Pneumatic Components' OR brand IN ('FESTO', 'SMC')
        ORDER BY unit_price_inr DESC
        LIMIT 10
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return self.format_slack_results(df, "💨 Pneumatic Components")
    
    def search_electrical_components(self):
        """Search for electrical components"""
        conn = self.connect_db()
        query = """
        SELECT part_number, description, brand, unit_price_inr, quantity, 
               total_value_inr, stock_status, category
        FROM silver_inventory_items 
        WHERE category = 'Electrical Components' OR brand IN ('Eaton', 'Siemens', 'Omron')
        ORDER BY unit_price_inr DESC
        LIMIT 10
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return self.format_slack_results(df, "⚡ Electrical Components")
    
    def search_cables_connectors(self):
        """Search for cables and connectors"""
        conn = self.connect_db()
        query = """
        SELECT part_number, description, brand, unit_price_inr, quantity, 
               total_value_inr, stock_status, category
        FROM silver_inventory_items 
        WHERE category = 'Cables & Connectors' OR brand IN ('LAPP', 'Phoenix')
        ORDER BY unit_price_inr DESC
        LIMIT 10
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return self.format_slack_results(df, "🔌 Cables & Connectors")
    
    def search_high_value_items(self):
        """Search for high-value items"""
        conn = self.connect_db()
        query = """
        SELECT part_number, description, brand, unit_price_inr, quantity, 
               total_value_inr, stock_status, category
        FROM silver_inventory_items 
        WHERE unit_price_inr > 10000
        ORDER BY unit_price_inr DESC
        LIMIT 10
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return self.format_slack_results(df, "💰 High Value Items")
    
    def search_low_value_items(self):
        """Search for low-value items"""
        conn = self.connect_db()
        query = """
        SELECT part_number, description, brand, unit_price_inr, quantity, 
               total_value_inr, stock_status, category
        FROM silver_inventory_items 
        WHERE unit_price_inr < 1000 AND unit_price_inr > 0
        ORDER BY unit_price_inr ASC
        LIMIT 10
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return self.format_slack_results(df, "💸 Low Value Items")
    
    def search_out_of_stock(self):
        """Search for out of stock items"""
        conn = self.connect_db()
        query = """
        SELECT part_number, description, brand, unit_price_inr, quantity, 
               total_value_inr, stock_status, category
        FROM silver_inventory_items 
        WHERE quantity = 0 AND unit_price_inr > 0
        ORDER BY unit_price_inr DESC
        LIMIT 10
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return self.format_slack_results(df, "🚨 Out of Stock Items")
    
    def search_in_stock(self):
        """Search for in-stock items"""
        conn = self.connect_db()
        query = """
        SELECT part_number, description, brand, unit_price_inr, quantity, 
               total_value_inr, stock_status, category
        FROM silver_inventory_items 
        WHERE quantity > 0
        ORDER BY unit_price_inr DESC
        LIMIT 10
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return self.format_slack_results(df, "✅ In Stock Items")
    
    def search_by_brand(self, brand):
        """Search by specific brand"""
        conn = self.connect_db()
        query = """
        SELECT part_number, description, brand, unit_price_inr, quantity, 
               total_value_inr, stock_status, category
        FROM silver_inventory_items 
        WHERE brand = ?
        ORDER BY unit_price_inr DESC
        LIMIT 10
        """
        df = pd.read_sql_query(query, conn, params=(brand,))
        conn.close()
        return self.format_slack_results(df, f"🏭 {brand} Products")
    
    def general_search(self, query):
        """General text search"""
        conn = self.connect_db()
        search_term = f"%{query}%"
        sql_query = """
        SELECT part_number, description, brand, unit_price_inr, quantity, 
               total_value_inr, stock_status, category
        FROM silver_inventory_items 
        WHERE part_number LIKE ? OR description LIKE ?
        ORDER BY unit_price_inr DESC
        LIMIT 10
        """
        df = pd.read_sql_query(sql_query, conn, params=(search_term, search_term))
        conn.close()
        return self.format_slack_results(df, f"🔍 Search Results for '{query}'")
    
    def format_slack_results(self, df, category):
        """Format search results for Slack"""
        if df.empty:
            return {
                'text': f"*{category}*\n\nNo results found. Try a different search term.",
                'attachments': []
            }
        
        # Create main message
        total_value = df['total_value_inr'].sum()
        message = f"*{category}*\n"
        message += f"Found {len(df)} items • Total Value: ₹{total_value:,.2f}\n\n"
        
        # Create attachments for each item
        attachments = []
        for _, row in df.iterrows():
            part_num = row['part_number'] or 'N/A'
            desc = row['description'] or 'N/A'
            brand = row['brand'] or 'Unknown'
            price = row['unit_price_inr']
            qty = row['quantity']
            total_val = row['total_value_inr']
            status = row['stock_status']
            
            # Get status emoji
            status_emoji = "✅" if status == "In Stock" else "⚠️" if status == "Low Stock" else "🚨"
            
            # Create attachment
            attachment = {
                "color": "good" if status == "In Stock" else "warning" if status == "Low Stock" else "danger",
                "fields": [
                    {
                        "title": f"{self.get_icon_for_item(row['category'], brand)} {part_num}",
                        "value": f"*{desc[:100]}{'...' if len(desc) > 100 else ''}*",
                        "short": False
                    },
                    {
                        "title": "Price",
                        "value": f"₹{price:,.2f}",
                        "short": True
                    },
                    {
                        "title": "Stock",
                        "value": f"{status_emoji} {qty} units",
                        "short": True
                    },
                    {
                        "title": "Brand",
                        "value": brand,
                        "short": True
                    },
                    {
                        "title": "Total Value",
                        "value": f"₹{total_val:,.2f}",
                        "short": True
                    }
                ]
            }
            attachments.append(attachment)
        
        return {
            'text': message,
            'attachments': attachments
        }
    
    def get_icon_for_item(self, category, brand):
        """Get appropriate icon for item based on category and brand"""
        if not category:
            category = "Other"
        
        icon_map = {
            'Servo Motors': '⚙️',
            'Motors & Drives': '🔧',
            'Pneumatic Components': '💨',
            'Electrical Components': '⚡',
            'Cables & Connectors': '🔌',
            'Sensors & Instrumentation': '📡',
            'Mechanical Components': '🔩',
            'Heating Elements': '🔥',
            'PLC & Control Systems': '💻',
            'Other Components': '📦'
        }
        
        # Brand-specific icons
        brand_icons = {
            'Mitsubishi': '🏭',
            'FESTO': '💨',
            'SMC': '🔧',
            'Eaton': '⚡',
            'Siemens': '🏢',
            'Omron': '🔬',
            'SICK': '👁️',
            'Phoenix': '🔌',
            'LAPP': '🔌'
        }
        
        icon = icon_map.get(category, '📦')
        if brand in brand_icons:
            icon = brand_icons[brand]
        
        return icon
    
    def get_inventory_summary(self):
        """Get overall inventory summary"""
        conn = self.connect_db()
        query = """
        SELECT 
            COUNT(*) as total_items,
            COUNT(DISTINCT brand) as total_brands,
            COUNT(DISTINCT category) as total_categories,
            SUM(unit_price_inr) as total_value,
            AVG(unit_price_inr) as avg_price,
            SUM(quantity) as total_quantity,
            SUM(total_value_inr) as total_inventory_value,
            COUNT(CASE WHEN stock_status = 'Low Stock' THEN 1 END) as low_stock_items,
            COUNT(CASE WHEN stock_status = 'Out of Stock' THEN 1 END) as out_of_stock_items
        FROM silver_inventory_items
        """
        result = conn.execute(query).fetchone()
        conn.close()
        
        message = "*🏭 Machinecraft Inventory Summary*\n\n"
        message += f"📦 Total Items: {result[0]:,}\n"
        message += f"🏷️ Brands: {result[1]:,}\n"
        message += f"📂 Categories: {result[2]:,}\n"
        message += f"💰 Total Value: ₹{result[3]:,.2f}\n"
        message += f"📊 Average Price: ₹{result[4]:,.2f}\n"
        message += f"📈 Total Quantity: {result[5]:,}\n"
        message += f"💎 Inventory Value: ₹{result[6]:,.2f}\n"
        message += f"⚠️ Low Stock: {result[7]:,}\n"
        message += f"🚨 Out of Stock: {result[8]:,}\n"
        
        return message
    
    def handle_message(self, event):
        """Handle incoming Slack messages"""
        try:
            # Get the message text
            text = event.get('text', '').lower()
            channel = event['channel']
            
            # Check if message mentions the bot or starts with inventory command
            if 'inventory' in text or 'stock' in text or 'search' in text:
                # Extract search query
                query = text.replace('inventory', '').replace('stock', '').replace('search', '').strip()
                
                if not query or query in ['summary', 'overview', 'total']:
                    # Return inventory summary
                    message = self.get_inventory_summary()
                    self.client.chat_postMessage(channel=channel, text=message)
                else:
                    # Perform search
                    results = self.natural_language_search(query)
                    self.client.chat_postMessage(
                        channel=channel,
                        text=results['text'],
                        attachments=results['attachments']
                    )
            
        except SlackApiError as e:
            print(f"Error posting message: {e.response['error']}")
        except Exception as e:
            print(f"Error handling message: {str(e)}")

def main():
    """Main function to run the Slack bot"""
    print("Starting Machinecraft Inventory Slack Bot...")
    
    # Check if Slack token is set
    if not os.environ.get("SLACK_BOT_TOKEN"):
        print("Error: SLACK_BOT_TOKEN environment variable not set")
        print("Please set your Slack bot token:")
        print("export SLACK_BOT_TOKEN='your-slack-bot-token-here'")
        return
    
    # Initialize bot
    bot = SlackInventoryBot()
    
    print("Bot initialized successfully!")
    print("Usage examples:")
    print("  - 'inventory servo motors'")
    print("  - 'inventory expensive items'")
    print("  - 'inventory mitsubishi'")
    print("  - 'inventory out of stock'")
    print("  - 'inventory summary'")
    
    # For now, just show that the bot is ready
    # In production, you would integrate this with Slack's Events API
    print("\nBot is ready! Integrate with Slack Events API to receive messages.")

if __name__ == "__main__":
    main()
