#!/usr/bin/env python3
"""
Script to upload the database to Railway
This creates a compressed version of the database for Railway deployment
"""

import os
import sqlite3
import gzip
import shutil
from pathlib import Path

def compress_database():
    """Compress the database for Railway upload"""
    db_path = "machinecraft_inventory_pipeline.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database file {db_path} not found!")
        return False
    
    # Get file size
    size_mb = os.path.getsize(db_path) / (1024 * 1024)
    print(f"📊 Database size: {size_mb:.2f} MB")
    
    # Compress the database
    compressed_path = "machinecraft_inventory_pipeline.db.gz"
    
    with open(db_path, 'rb') as f_in:
        with gzip.open(compressed_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    
    compressed_size = os.path.getsize(compressed_path) / (1024 * 1024)
    print(f"📦 Compressed size: {compressed_size:.2f} MB")
    print(f"💾 Compression ratio: {(1 - compressed_size/size_mb)*100:.1f}%")
    
    return compressed_path

def create_sample_database():
    """Create a sample database for testing"""
    db_path = "sample_inventory.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create the silver_inventory_items table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS silver_inventory_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            part_number TEXT,
            description TEXT,
            brand TEXT,
            unit_price_inr REAL,
            quantity INTEGER,
            total_value_inr REAL,
            stock_status TEXT,
            category TEXT
        )
    ''')
    
    # Insert sample data
    sample_items = [
        ('HG-SR7024B', '33.4 Nm, 7kW, 2000 RPM servo motor', 'Mitsubishi', 245400.0, 5, 1227000.0, 'In Stock', 'Servo Motors'),
        ('MR-J4-200B4', 'Servo Amplifier 200W', 'Mitsubishi', 143400.0, 11, 1577400.0, 'In Stock', 'Servo Motors'),
        ('PUNH-6X1-BL', 'Pneumatic fitting', 'FESTO', 100.0, 200, 20000.0, 'In Stock', 'Pneumatic Components'),
        ('XTCD9-11', 'Contactor 9A, 230V AC', 'Eaton', 2500.0, 15, 37500.0, 'In Stock', 'Electrical Components'),
        ('LAPP-001', 'Control cable 0.5mm²', 'LAPP', 50.0, 1000, 50000.0, 'In Stock', 'Cables & Connectors'),
    ]
    
    for item in sample_items:
        cursor.execute('''
            INSERT INTO silver_inventory_items 
            (part_number, description, brand, unit_price_inr, quantity, total_value_inr, stock_status, category)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', item)
    
    conn.commit()
    conn.close()
    
    print(f"✅ Created sample database: {db_path}")
    return db_path

if __name__ == "__main__":
    print("🚀 Preparing database for Railway deployment...")
    
    # Try to compress the main database
    if os.path.exists("machinecraft_inventory_pipeline.db"):
        compressed = compress_database()
        if compressed:
            print(f"✅ Compressed database ready: {compressed}")
            print("📤 Upload this file to Railway Storage")
    else:
        print("⚠️  Main database not found, creating sample database...")
        sample_db = create_sample_database()
        print(f"📤 Upload {sample_db} to Railway Storage as 'machinecraft_inventory_pipeline.db'")
    
    print("\n📋 Next steps:")
    print("1. Go to Railway dashboard → Storage tab")
    print("2. Upload the database file")
    print("3. Redeploy your service")
    print("4. Test the health endpoint: https://your-app.railway.app/health")
