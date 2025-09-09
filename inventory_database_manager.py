#!/usr/bin/env python3
"""
Machinecraft Inventory Database Manager
Query interface for the Silver database
"""

import sqlite3
import pandas as pd
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

class InventoryDatabaseManager:
    def __init__(self, db_path: str = "machinecraft_inventory_pipeline.db"):
        self.db_path = db_path
        self.conn = None
    
    def connect(self):
        """Connect to the database"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        print(f"Connected to database: {self.db_path}")
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            print("Database connection closed")
    
    def get_inventory_summary(self) -> Dict[str, Any]:
        """Get overall inventory summary"""
        query = "SELECT * FROM gold_inventory_summary"
        result = pd.read_sql_query(query, self.conn)
        return result.to_dict('records')[0] if not result.empty else {}
    
    def get_high_value_items(self, limit: int = 20) -> pd.DataFrame:
        """Get high-value items (>₹10K)"""
        query = f"""
        SELECT part_number, description, brand, category, 
               unit_price_inr, quantity, total_value_inr, stock_status
        FROM gold_high_value_items 
        ORDER BY total_value_inr DESC 
        LIMIT {limit}
        """
        return pd.read_sql_query(query, self.conn)
    
    def get_low_stock_alerts(self) -> pd.DataFrame:
        """Get low stock alerts"""
        query = """
        SELECT part_number, description, brand, category,
               unit_price_inr, quantity, min_stock, total_value_inr
        FROM gold_low_stock_alerts
        ORDER BY total_value_inr DESC
        """
        return pd.read_sql_query(query, self.conn)
    
    def get_brand_analysis(self) -> pd.DataFrame:
        """Get brand analysis"""
        query = """
        SELECT brand, item_count, total_value, avg_price, 
               min_price, max_price, total_quantity, total_inventory_value
        FROM gold_brand_analysis
        ORDER BY total_inventory_value DESC
        """
        return pd.read_sql_query(query, self.conn)
    
    def get_category_analysis(self) -> pd.DataFrame:
        """Get category analysis"""
        query = """
        SELECT category, item_count, total_value, avg_price,
               total_quantity, total_inventory_value
        FROM gold_category_analysis
        ORDER BY total_inventory_value DESC
        """
        return pd.read_sql_query(query, self.conn)
    
    def search_items(self, search_term: str, limit: int = 50) -> pd.DataFrame:
        """Search items by part number or description"""
        query = """
        SELECT part_number, description, brand, category,
               unit_price_inr, quantity, total_value_inr, stock_status
        FROM silver_inventory_items
        WHERE part_number LIKE ? OR description LIKE ?
        ORDER BY total_value_inr DESC
        LIMIT ?
        """
        search_pattern = f"%{search_term}%"
        return pd.read_sql_query(query, self.conn, params=(search_pattern, search_pattern, limit))
    
    def get_items_by_brand(self, brand: str) -> pd.DataFrame:
        """Get all items for a specific brand"""
        query = """
        SELECT part_number, description, category, unit_price_inr,
               quantity, total_value_inr, stock_status
        FROM silver_inventory_items
        WHERE brand = ?
        ORDER BY total_value_inr DESC
        """
        return pd.read_sql_query(query, self.conn, params=(brand,))
    
    def get_items_by_category(self, category: str) -> pd.DataFrame:
        """Get all items for a specific category"""
        query = """
        SELECT part_number, description, brand, unit_price_inr,
               quantity, total_value_inr, stock_status
        FROM silver_inventory_items
        WHERE category = ?
        ORDER BY total_value_inr DESC
        """
        return pd.read_sql_query(query, self.conn, params=(category,))
    
    def export_to_excel(self, output_file: str = "inventory_export.xlsx"):
        """Export all data to Excel with multiple sheets"""
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Summary
            summary = self.get_inventory_summary()
            summary_df = pd.DataFrame([summary])
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # High value items
            high_value = self.get_high_value_items(100)
            high_value.to_excel(writer, sheet_name='High Value Items', index=False)
            
            # Low stock alerts
            low_stock = self.get_low_stock_alerts()
            low_stock.to_excel(writer, sheet_name='Low Stock Alerts', index=False)
            
            # Brand analysis
            brand_analysis = self.get_brand_analysis()
            brand_analysis.to_excel(writer, sheet_name='Brand Analysis', index=False)
            
            # Category analysis
            category_analysis = self.get_category_analysis()
            category_analysis.to_excel(writer, sheet_name='Category Analysis', index=False)
            
            # All items
            all_items = pd.read_sql_query("""
                SELECT part_number, description, brand, category,
                       unit_price_inr, quantity, min_stock, total_value_inr,
                       stock_status, price_range, source_file
                FROM silver_inventory_items
                ORDER BY total_value_inr DESC
            """, self.conn)
            all_items.to_excel(writer, sheet_name='All Items', index=False)
        
        print(f"Data exported to: {output_file}")
    
    def print_dashboard(self):
        """Print a text-based dashboard"""
        print("\n" + "="*80)
        print("MACHINECRAFT INVENTORY DASHBOARD")
        print("="*80)
        
        # Summary
        summary = self.get_inventory_summary()
        if summary:
            print(f"Total Items: {summary.get('total_items', 0):,}")
            print(f"Total Brands: {summary.get('total_brands', 0):,}")
            print(f"Total Categories: {summary.get('total_categories', 0):,}")
            print(f"Total Value: ₹{summary.get('total_value', 0):,.2f}")
            print(f"Average Price: ₹{summary.get('avg_price', 0):,.2f}")
            print(f"Total Quantity: {summary.get('total_quantity', 0):,}")
            print(f"Low Stock Items: {summary.get('low_stock_items', 0):,}")
            print(f"Out of Stock Items: {summary.get('out_of_stock_items', 0):,}")
        
        print("\n" + "-"*80)
        print("TOP 10 BRANDS BY VALUE")
        print("-"*80)
        brand_analysis = self.get_brand_analysis()
        for _, row in brand_analysis.head(10).iterrows():
            print(f"{row['brand']:20} | Items: {row['item_count']:4} | Value: ₹{row['total_inventory_value']:10,.2f}")
        
        print("\n" + "-"*80)
        print("TOP 10 CATEGORIES BY VALUE")
        print("-"*80)
        category_analysis = self.get_category_analysis()
        for _, row in category_analysis.head(10).iterrows():
            print(f"{row['category']:30} | Items: {row['item_count']:4} | Value: ₹{row['total_inventory_value']:10,.2f}")
        
        print("\n" + "-"*80)
        print("HIGH VALUE ITEMS (>₹10K)")
        print("-"*80)
        high_value = self.get_high_value_items(10)
        for _, row in high_value.iterrows():
            print(f"{row['part_number']:15} | {row['description'][:40]:40} | ₹{row['total_value_inr']:10,.2f}")
        
        print("\n" + "-"*80)
        print("LOW STOCK ALERTS")
        print("-"*80)
        low_stock = self.get_low_stock_alerts()
        if not low_stock.empty:
            for _, row in low_stock.head(10).iterrows():
                print(f"{row['part_number']:15} | {row['description'][:40]:40} | Stock: {row['quantity']:3} | Min: {row['min_stock']:3}")
        else:
            print("No low stock alerts")
        
        print("="*80)

def main():
    """Main function for testing"""
    db_manager = InventoryDatabaseManager()
    
    try:
        db_manager.connect()
        db_manager.print_dashboard()
        
        # Export to Excel
        db_manager.export_to_excel("machinecraft_inventory_dashboard.xlsx")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db_manager.close()

if __name__ == "__main__":
    main()
