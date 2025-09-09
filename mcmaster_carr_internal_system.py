#!/usr/bin/env python3
"""
McMaster-Carr Style Internal Inventory System
Natural language search + web scraping + visual interface
"""

import sqlite3
import pandas as pd
import requests
from bs4 import BeautifulSoup
import json
import re
from flask import Flask, render_template, request, jsonify
import os
from pathlib import Path

class McMasterCarrInternalSystem:
    def __init__(self, db_path="machinecraft_inventory_pipeline.db"):
        self.db_path = db_path
        self.app = Flask(__name__)
        self.setup_routes()
        
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
            """
            df = pd.read_sql_query(query, conn)
        
        conn.close()
        return self.format_results(df, "Servo Motors")
    
    def search_pneumatic_components(self):
        """Search for pneumatic components"""
        conn = self.connect_db()
        query = """
        SELECT part_number, description, brand, unit_price_inr, quantity, 
               total_value_inr, stock_status, category
        FROM silver_inventory_items 
        WHERE category = 'Pneumatic Components' OR brand IN ('FESTO', 'SMC')
        ORDER BY unit_price_inr DESC
        LIMIT 50
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return self.format_results(df, "Pneumatic Components")
    
    def search_electrical_components(self):
        """Search for electrical components"""
        conn = self.connect_db()
        query = """
        SELECT part_number, description, brand, unit_price_inr, quantity, 
               total_value_inr, stock_status, category
        FROM silver_inventory_items 
        WHERE category = 'Electrical Components' OR brand IN ('Eaton', 'Siemens', 'Omron')
        ORDER BY unit_price_inr DESC
        LIMIT 50
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return self.format_results(df, "Electrical Components")
    
    def search_cables_connectors(self):
        """Search for cables and connectors"""
        conn = self.connect_db()
        query = """
        SELECT part_number, description, brand, unit_price_inr, quantity, 
               total_value_inr, stock_status, category
        FROM silver_inventory_items 
        WHERE category = 'Cables & Connectors' OR brand IN ('LAPP', 'Phoenix')
        ORDER BY unit_price_inr DESC
        LIMIT 50
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return self.format_results(df, "Cables & Connectors")
    
    def search_high_value_items(self):
        """Search for high-value items"""
        conn = self.connect_db()
        query = """
        SELECT part_number, description, brand, unit_price_inr, quantity, 
               total_value_inr, stock_status, category
        FROM silver_inventory_items 
        WHERE unit_price_inr > 10000
        ORDER BY unit_price_inr DESC
        LIMIT 50
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return self.format_results(df, "High Value Items")
    
    def search_low_value_items(self):
        """Search for low-value items"""
        conn = self.connect_db()
        query = """
        SELECT part_number, description, brand, unit_price_inr, quantity, 
               total_value_inr, stock_status, category
        FROM silver_inventory_items 
        WHERE unit_price_inr < 1000 AND unit_price_inr > 0
        ORDER BY unit_price_inr ASC
        LIMIT 50
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return self.format_results(df, "Low Value Items")
    
    def search_out_of_stock(self):
        """Search for out of stock items"""
        conn = self.connect_db()
        query = """
        SELECT part_number, description, brand, unit_price_inr, quantity, 
               total_value_inr, stock_status, category
        FROM silver_inventory_items 
        WHERE quantity = 0 AND unit_price_inr > 0
        ORDER BY unit_price_inr DESC
        LIMIT 50
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return self.format_results(df, "Out of Stock Items")
    
    def search_in_stock(self):
        """Search for in-stock items"""
        conn = self.connect_db()
        query = """
        SELECT part_number, description, brand, unit_price_inr, quantity, 
               total_value_inr, stock_status, category
        FROM silver_inventory_items 
        WHERE quantity > 0
        ORDER BY unit_price_inr DESC
        LIMIT 50
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return self.format_results(df, "In Stock Items")
    
    def search_by_brand(self, brand):
        """Search by specific brand"""
        conn = self.connect_db()
        query = """
        SELECT part_number, description, brand, unit_price_inr, quantity, 
               total_value_inr, stock_status, category
        FROM silver_inventory_items 
        WHERE brand = ?
        ORDER BY unit_price_inr DESC
        LIMIT 50
        """
        df = pd.read_sql_query(query, conn, params=(brand,))
        conn.close()
        return self.format_results(df, f"{brand} Products")
    
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
        LIMIT 50
        """
        df = pd.read_sql_query(sql_query, conn, params=(search_term, search_term))
        conn.close()
        return self.format_results(df, f"Search Results for '{query}'")
    
    def format_results(self, df, category):
        """Format search results with icons and categories"""
        if df.empty:
            return {
                'category': category,
                'count': 0,
                'items': [],
                'total_value': 0
            }
        
        items = []
        for _, row in df.iterrows():
            item = {
                'part_number': row['part_number'] or 'N/A',
                'description': row['description'] or 'N/A',
                'brand': row['brand'] or 'Unknown',
                'price': row['unit_price_inr'],
                'quantity': row['quantity'],
                'total_value': row['total_value_inr'],
                'stock_status': row['stock_status'],
                'category': row['category'] or 'Uncategorized',
                'icon': self.get_icon_for_item(row['category'], row['brand']),
                'price_formatted': f"₹{row['unit_price_inr']:,.2f}",
                'total_value_formatted': f"₹{row['total_value_inr']:,.2f}"
            }
            items.append(item)
        
        return {
            'category': category,
            'count': len(items),
            'items': items,
            'total_value': df['total_value_inr'].sum()
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
    
    def web_scrape_product_info(self, part_number, brand):
        """Web scrape additional product information"""
        try:
            # This would integrate with actual manufacturer websites
            # For now, return mock data
            return {
                'datasheet_url': f"https://example.com/datasheet/{part_number}",
                '3d_model_url': f"https://example.com/3d/{part_number}",
                'specifications': self.get_mock_specifications(part_number, brand),
                'compatible_parts': self.get_compatible_parts(part_number),
                'lead_time': '2-4 weeks',
                'warranty': '1 year'
            }
        except:
            return None
    
    def get_mock_specifications(self, part_number, brand):
        """Get mock specifications for a part"""
        if 'HG-SR' in part_number:
            return {
                'Power': '2-7 kW',
                'Torque': '9.5-33.4 Nm',
                'Speed': '2000-3000 RPM',
                'Voltage': '400V AC',
                'Weight': '2.5-8.5 kg'
            }
        elif 'MR-J' in part_number:
            return {
                'Power': '100-700W',
                'Communication': 'SSCNET III',
                'Input': '24V DC',
                'Output': '3-phase AC',
                'Weight': '0.5-2.0 kg'
            }
        else:
            return {
                'Type': 'Industrial Component',
                'Brand': brand,
                'Category': 'Automation'
            }
    
    def get_compatible_parts(self, part_number):
        """Get compatible parts for a given part number"""
        # This would query the database for compatible parts
        return [
            f"{part_number}-CABLE",
            f"{part_number}-BRACKET",
            f"{part_number}-CONNECTOR"
        ]
    
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            return render_template('index.html')
        
        @self.app.route('/search')
        def search():
            query = request.args.get('q', '')
            if not query:
                return jsonify({'error': 'No search query provided'})
            
            results = self.natural_language_search(query)
            return jsonify(results)
        
        @self.app.route('/product/<part_number>')
        def product_detail(part_number):
            conn = self.connect_db()
            query = """
            SELECT * FROM silver_inventory_items 
            WHERE part_number = ?
            """
            df = pd.read_sql_query(query, conn, params=(part_number,))
            conn.close()
            
            if df.empty:
                return jsonify({'error': 'Product not found'})
            
            product = df.iloc[0].to_dict()
            product['icon'] = self.get_icon_for_item(product['category'], product['brand'])
            product['web_info'] = self.web_scrape_product_info(part_number, product['brand'])
            
            return jsonify(product)
        
        @self.app.route('/categories')
        def categories():
            conn = self.connect_db()
            query = """
            SELECT category, COUNT(*) as count, SUM(unit_price_inr) as total_value
            FROM silver_inventory_items 
            WHERE category IS NOT NULL AND category != 'Uncategorized'
            GROUP BY category
            ORDER BY total_value DESC
            """
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            categories = []
            for _, row in df.iterrows():
                categories.append({
                    'name': row['category'],
                    'count': row['count'],
                    'total_value': row['total_value'],
                    'icon': self.get_icon_for_item(row['category'], None)
                })
            
            return jsonify(categories)
    
    def run(self, debug=True, port=5000):
        """Run the Flask application"""
        print(f"Starting McMaster-Carr Internal System...")
        print(f"Access at: http://localhost:{port}")
        print(f"Search examples:")
        print(f"  - 'servo motors'")
        print(f"  - 'expensive items'")
        print(f"  - 'mitsubishi'")
        print(f"  - 'out of stock'")
        print(f"  - 'pneumatic components'")
        
        self.app.run(debug=debug, port=port)

def create_html_templates():
    """Create HTML templates for the web interface"""
    
    # Create templates directory
    os.makedirs('templates', exist_ok=True)
    
    # Main index.html template
    index_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Machinecraft Internal Inventory System</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
        }
        .search-container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .search-box {
            width: 100%;
            padding: 15px;
            font-size: 18px;
            border: 2px solid #ddd;
            border-radius: 25px;
            outline: none;
            transition: border-color 0.3s;
        }
        .search-box:focus {
            border-color: #667eea;
        }
        .search-button {
            background: #667eea;
            color: white;
            border: none;
            padding: 15px 30px;
            font-size: 18px;
            border-radius: 25px;
            cursor: pointer;
            margin-left: 10px;
            transition: background 0.3s;
        }
        .search-button:hover {
            background: #5a6fd8;
        }
        .results {
            margin-top: 30px;
        }
        .item-card {
            background: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 15px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }
        .item-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }
        .item-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        .part-number {
            font-weight: bold;
            font-size: 18px;
            color: #333;
        }
        .price {
            font-size: 20px;
            font-weight: bold;
            color: #667eea;
        }
        .description {
            color: #666;
            margin-bottom: 10px;
        }
        .item-details {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .brand {
            background: #e3f2fd;
            color: #1976d2;
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 12px;
        }
        .stock-status {
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 12px;
            font-weight: bold;
        }
        .in-stock {
            background: #e8f5e8;
            color: #2e7d32;
        }
        .low-stock {
            background: #fff3e0;
            color: #f57c00;
        }
        .out-of-stock {
            background: #ffebee;
            color: #c62828;
        }
        .loading {
            text-align: center;
            padding: 20px;
            color: #666;
        }
        .error {
            background: #ffebee;
            color: #c62828;
            padding: 15px;
            border-radius: 5px;
            margin-top: 20px;
        }
        .categories {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-bottom: 20px;
        }
        .category-tag {
            background: #f0f0f0;
            padding: 8px 15px;
            border-radius: 20px;
            cursor: pointer;
            transition: background 0.3s;
        }
        .category-tag:hover {
            background: #667eea;
            color: white;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏭 Machinecraft Internal Inventory System</h1>
        <p>Search through 10.5M+ inventory items with natural language</p>
    </div>
    
    <div class="search-container">
        <div class="search-form">
            <input type="text" class="search-box" id="searchInput" placeholder="Search for servo motors, pneumatic components, electrical parts...">
            <button class="search-button" onclick="search()">Search</button>
        </div>
        
        <div class="categories" id="categories">
            <!-- Categories will be loaded here -->
        </div>
        
        <div class="results" id="results">
            <div class="loading">Enter a search term to get started...</div>
        </div>
    </div>

    <script>
        // Load categories on page load
        fetch('/categories')
            .then(response => response.json())
            .then(data => {
                const categoriesDiv = document.getElementById('categories');
                data.forEach(category => {
                    const tag = document.createElement('div');
                    tag.className = 'category-tag';
                    tag.innerHTML = `${category.icon} ${category.name} (${category.count})`;
                    tag.onclick = () => search(category.name);
                    categoriesDiv.appendChild(tag);
                });
            });

        function search(query = null) {
            const searchInput = document.getElementById('searchInput');
            const queryText = query || searchInput.value;
            
            if (!queryText.trim()) return;
            
            const resultsDiv = document.getElementById('results');
            resultsDiv.innerHTML = '<div class="loading">Searching...</div>';
            
            fetch(`/search?q=${encodeURIComponent(queryText)}`)
                .then(response => response.json())
                .then(data => {
                    displayResults(data);
                })
                .catch(error => {
                    resultsDiv.innerHTML = `<div class="error">Error: ${error.message}</div>`;
                });
        }
        
        function displayResults(data) {
            const resultsDiv = document.getElementById('results');
            
            if (data.error) {
                resultsDiv.innerHTML = `<div class="error">${data.error}</div>`;
                return;
            }
            
            if (data.count === 0) {
                resultsDiv.innerHTML = '<div class="loading">No results found. Try a different search term.</div>';
                return;
            }
            
            let html = `
                <h3>${data.category} (${data.count} items)</h3>
                <p>Total Value: ₹${data.total_value.toLocaleString()}</p>
            `;
            
            data.items.forEach(item => {
                const stockClass = item.stock_status === 'In Stock' ? 'in-stock' : 
                                 item.stock_status === 'Low Stock' ? 'low-stock' : 'out-of-stock';
                
                html += `
                    <div class="item-card" onclick="showProductDetail('${item.part_number}')">
                        <div class="item-header">
                            <div class="part-number">${item.icon} ${item.part_number}</div>
                            <div class="price">${item.price_formatted}</div>
                        </div>
                        <div class="description">${item.description}</div>
                        <div class="item-details">
                            <div>
                                <span class="brand">${item.brand}</span>
                                <span class="stock-status ${stockClass}">${item.stock_status}</span>
                            </div>
                            <div>
                                Qty: ${item.quantity} | Total: ${item.total_value_formatted}
                            </div>
                        </div>
                    </div>
                `;
            });
            
            resultsDiv.innerHTML = html;
        }
        
        function showProductDetail(partNumber) {
            fetch(`/product/${partNumber}`)
                .then(response => response.json())
                .then(data => {
                    alert(`Product Details:\\n\\nPart: ${data.part_number}\\nDescription: ${data.description}\\nBrand: ${data.brand}\\nPrice: ₹${data.unit_price_inr.toLocaleString()}\\nStock: ${data.quantity}\\nCategory: ${data.category}`);
                });
        }
        
        // Allow Enter key to search
        document.getElementById('searchInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                search();
            }
        });
    </script>
</body>
</html>
    """
    
    with open('templates/index.html', 'w') as f:
        f.write(index_html)

def main():
    """Main function to run the system"""
    print("Creating McMaster-Carr Style Internal Inventory System...")
    
    # Create HTML templates
    create_html_templates()
    
    # Initialize and run the system
    system = McMasterCarrInternalSystem()
    system.run(debug=True, port=5000)

if __name__ == "__main__":
    main()
