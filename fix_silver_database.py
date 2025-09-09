#!/usr/bin/env python3
"""
Fix Silver Database - Properly extract data from Bronze layer
"""

import sqlite3
import json
import pandas as pd
import re
from pathlib import Path

def fix_silver_database():
    """Fix the Silver database by properly extracting data from Bronze"""
    
    conn = sqlite3.connect('machinecraft_inventory_pipeline.db')
    conn.row_factory = sqlite3.Row
    
    # Clear existing Silver data
    conn.execute('DELETE FROM silver_inventory_items')
    
    # Get all Bronze data
    cursor = conn.execute('SELECT id, source_file, raw_data FROM bronze_inventory_raw WHERE processing_status = "ingested"')
    
    processed_count = 0
    
    for row in cursor.fetchall():
        try:
            raw_data = json.loads(row['raw_data'])
            source_file = row['source_file']
            
            # Extract brand from filename
            brand = extract_brand_from_filename(source_file)
            
            # Process each sheet
            for sheet_name, sheet_data in raw_data.items():
                if not isinstance(sheet_data, dict) or 'data' not in sheet_data or not sheet_data['data']:
                    continue
                
                df = pd.DataFrame(sheet_data['data'])
                columns = [col.lower().strip() for col in df.columns]
                
                # Map columns to standard fields
                part_number_col = None
                description_col = None
                price_col = None
                quantity_col = None
                min_stock_col = None
                
                # Find matching columns
                for i, col in enumerate(columns):
                    if any(keyword in col for keyword in ['part', 'item no', 'model', 'sku', 'code']):
                        part_number_col = df.columns[i]
                    elif any(keyword in col for keyword in ['description', 'desc', 'name', 'item description']):
                        description_col = df.columns[i]
                    elif any(keyword in col for keyword in ['price', 'cost', 'rate', 'value', 'amount']):
                        price_col = df.columns[i]
                    elif any(keyword in col for keyword in ['qty', 'quantity', 'stock', 'available']):
                        quantity_col = df.columns[i]
                    elif any(keyword in col for keyword in ['min', 'maintain', 'reorder']):
                        min_stock_col = df.columns[i]
                
                # Process each row
                for _, row_data in df.iterrows():
                    try:
                        # Extract data
                        part_number = clean_text(row_data.get(part_number_col, '')) if part_number_col else ''
                        description = clean_text(row_data.get(description_col, '')) if description_col else ''
                        price = clean_price(row_data.get(price_col, 0)) if price_col else 0.0
                        quantity = clean_quantity(row_data.get(quantity_col, 0)) if quantity_col else 0
                        min_stock = clean_quantity(row_data.get(min_stock_col, 0)) if min_stock_col else 0
                        
                        # Skip empty rows
                        if not part_number and not description:
                            continue
                        
                        # Categorize based on description and part number
                        category = categorize_item(part_number, description, brand)
                        
                        # Insert into Silver
                        conn.execute("""
                            INSERT INTO silver_inventory_items 
                            (part_number, description, brand, category, unit_price_inr, 
                             quantity, min_stock, source_file, source_sheet, 
                             ai_confidence, validation_status)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            part_number,
                            description,
                            brand,
                            category,
                            price,
                            quantity,
                            min_stock,
                            Path(source_file).name,
                            sheet_name,
                            'high',
                            'validated'
                        ))
                        
                        processed_count += 1
                        
                    except Exception as e:
                        print(f"Error processing row: {e}")
                        continue
                        
        except Exception as e:
            print(f"Error processing file {row['source_file']}: {e}")
            continue
    
    conn.commit()
    print(f"Fixed Silver database: {processed_count} items processed")
    
    # Show updated statistics
    total_items = conn.execute('SELECT COUNT(*) FROM silver_inventory_items').fetchone()[0]
    items_with_prices = conn.execute('SELECT COUNT(*) FROM silver_inventory_items WHERE unit_price_inr > 0').fetchone()[0]
    items_with_brands = conn.execute('SELECT COUNT(*) FROM silver_inventory_items WHERE brand != "Unknown"').fetchone()[0]
    
    print(f"Total items: {total_items:,}")
    print(f"Items with prices: {items_with_prices:,}")
    print(f"Items with brands: {items_with_brands:,}")
    
    conn.close()

def extract_brand_from_filename(filename):
    """Extract brand from filename"""
    filename = Path(filename).stem.lower()
    
    brand_mappings = {
        'mitsubishi': 'Mitsubishi',
        'festo': 'FESTO',
        'smc': 'SMC',
        'eaton': 'Eaton',
        'omron': 'Omron',
        'sick': 'SICK',
        'phoenix': 'Phoenix',
        'lapp': 'LAPP',
        'siemens': 'Siemens',
        'bearing': 'Bearing',
        'cylinder': 'Cylinder',
        'gear': 'Gearbox',
        'heater': 'Heater',
        'ceramix': 'CERAMIX',
        'crydom': 'CRYDOM',
        'ebm': 'EBM',
        'elstien': 'Elstien',
        'grand': 'Grand Polycoat',
        'hicool': 'Hicool',
        'indo': 'Indo Electricals',
        'nvent': 'Nvent Hoffman',
        'precision': 'Precision Valve',
        'pnf': 'PNF',
        'wohner': 'Wohner',
        'autonics': 'Autonics',
        'albro': 'Albro',
        'apratek': 'Apratek',
        'murr': 'Murr',
        'bonfiglioli': 'Bonfiglioli',
        'becker': 'Becker',
        'sunchu': 'Sunchu',
        'yyc': 'YYC',
        'hetronik': 'Hetronik',
        'flexicab': 'Flexicab',
        'hrc': 'HRC',
        'iac': 'IAC',
        'lathe': 'Lathe',
        'trinity': 'Trinity',
        'teknic': 'Teknic',
        'unison': 'Unison',
        'pneumax': 'Pneumax'
    }
    
    for key, brand in brand_mappings.items():
        if key in filename:
            return brand
    return 'Unknown'

def clean_text(text):
    """Clean text fields"""
    if pd.isna(text):
        return ""
    return str(text).strip()

def clean_price(price):
    """Clean price fields"""
    if pd.isna(price):
        return 0.0
    
    price_str = str(price).strip()
    # Remove currency symbols and text
    price_str = re.sub(r'[₹$€£,₹\s]', '', price_str)
    price_str = re.sub(r'[a-zA-Z\s]', '', price_str)
    
    try:
        return float(price_str)
    except:
        return 0.0

def clean_quantity(qty):
    """Clean quantity fields"""
    if pd.isna(qty):
        return 0
    try:
        return int(float(qty))
    except:
        return 0

def categorize_item(part_number, description, brand):
    """Categorize item based on description and part number"""
    desc_lower = description.lower()
    part_lower = part_number.lower()
    
    # Pneumatic components
    if any(keyword in desc_lower for keyword in ['pneumatic', 'cylinder', 'valve', 'festo', 'smc', 'connector', 'fitting']):
        return 'Pneumatic Components'
    
    # Electrical components
    elif any(keyword in desc_lower for keyword in ['contactor', 'mcb', 'mccb', 'relay', 'switch', 'electrical', 'eaton', 'siemens']):
        return 'Electrical Components'
    
    # Motors & Drives
    elif any(keyword in desc_lower for keyword in ['motor', 'servo', 'drive', 'mitsubishi', 'gear', 'gearbox']):
        return 'Motors & Drives'
    
    # Cables & Connectors
    elif any(keyword in desc_lower for keyword in ['cable', 'wire', 'connector', 'lapp', 'phoenix']):
        return 'Cables & Connectors'
    
    # Sensors & Instrumentation
    elif any(keyword in desc_lower for keyword in ['sensor', 'sick', 'omron', 'reed switch', 'proximity']):
        return 'Sensors & Instrumentation'
    
    # Mechanical Components
    elif any(keyword in desc_lower for keyword in ['bearing', 'sprocket', 'chain', 'linear', 'rail']):
        return 'Mechanical Components'
    
    # Heating Elements
    elif any(keyword in desc_lower for keyword in ['heater', 'heating', 'ceramic', 'ceramix']):
        return 'Heating Elements'
    
    # PLC & Control Systems
    elif any(keyword in desc_lower for keyword in ['plc', 'control', 'programmable', 'fx2n', 'fx3u']):
        return 'PLC & Control Systems'
    
    else:
        return 'Other Components'

if __name__ == "__main__":
    fix_silver_database()
