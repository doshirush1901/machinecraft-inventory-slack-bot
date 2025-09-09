#!/usr/bin/env python3
"""
Populate Silver Database from Bronze Layer
"""

import sqlite3
import json
import pandas as pd
import re
from pathlib import Path

def populate_silver():
    conn = sqlite3.connect('machinecraft_inventory_pipeline.db')
    conn.row_factory = sqlite3.Row
    
    # Clear existing Silver data
    conn.execute('DELETE FROM silver_inventory_items')
    
    # Get all Bronze data
    cursor = conn.execute('SELECT source_file, raw_data FROM bronze_inventory_raw')
    processed_count = 0
    
    for row in cursor.fetchall():
        try:
            raw_data = json.loads(row['raw_data'])
            source_file = row['source_file']
            
            # Extract brand from filename
            filename = Path(source_file).stem.lower()
            brand = 'Unknown'
            if 'mitsubishi' in filename:
                brand = 'Mitsubishi'
            elif 'festo' in filename:
                brand = 'FESTO'
            elif 'smc' in filename:
                brand = 'SMC'
            elif 'eaton' in filename:
                brand = 'Eaton'
            elif 'omron' in filename:
                brand = 'Omron'
            elif 'sick' in filename:
                brand = 'SICK'
            elif 'phoenix' in filename:
                brand = 'Phoenix'
            elif 'lapp' in filename:
                brand = 'LAPP'
            elif 'siemens' in filename:
                brand = 'Siemens'
            elif 'bearing' in filename:
                brand = 'Bearing'
            elif 'cylinder' in filename:
                brand = 'Cylinder'
            elif 'ceramix' in filename:
                brand = 'CERAMIX'
            elif 'crydom' in filename:
                brand = 'CRYDOM'
            elif 'ebm' in filename:
                brand = 'EBM'
            elif 'elstien' in filename:
                brand = 'Elstien'
            elif 'grand' in filename:
                brand = 'Grand Polycoat'
            elif 'hicool' in filename:
                brand = 'Hicool'
            elif 'indo' in filename:
                brand = 'Indo Electricals'
            elif 'nvent' in filename:
                brand = 'Nvent Hoffman'
            elif 'precision' in filename:
                brand = 'Precision Valve'
            elif 'pnf' in filename:
                brand = 'PNF'
            elif 'wohner' in filename:
                brand = 'Wohner'
            elif 'autonics' in filename:
                brand = 'Autonics'
            elif 'albro' in filename:
                brand = 'Albro'
            elif 'apratek' in filename:
                brand = 'Apratek'
            elif 'murr' in filename:
                brand = 'Murr'
            elif 'bonfiglioli' in filename:
                brand = 'Bonfiglioli'
            elif 'becker' in filename:
                brand = 'Becker'
            elif 'sunchu' in filename:
                brand = 'Sunchu'
            elif 'yyc' in filename:
                brand = 'YYC'
            elif 'hetronik' in filename:
                brand = 'Hetronik'
            elif 'flexicab' in filename:
                brand = 'Flexicab'
            elif 'hrc' in filename:
                brand = 'HRC'
            elif 'iac' in filename:
                brand = 'IAC'
            elif 'lathe' in filename:
                brand = 'Lathe'
            elif 'trinity' in filename:
                brand = 'Trinity'
            elif 'teknic' in filename:
                brand = 'Teknic'
            elif 'unison' in filename:
                brand = 'Unison'
            elif 'pneumax' in filename:
                brand = 'Pneumax'
            
            # Process each sheet
            for sheet_name, sheet_data in raw_data.items():
                if not isinstance(sheet_data, dict) or 'data' not in sheet_data or not sheet_data['data']:
                    continue
                
                df = pd.DataFrame(sheet_data['data'])
                
                # Process each row
                for _, row_data in df.iterrows():
                    try:
                        # Extract data - look for common column patterns
                        part_number = ''
                        description = ''
                        price = 0.0
                        quantity = 0
                        min_stock = 0
                        
                        # Look for part number
                        for col in df.columns:
                            if any(keyword in col.lower() for keyword in ['part', 'item no', 'model', 'sku', 'code']):
                                val = str(row_data[col]).strip()
                                if val and val != 'nan' and val != 'None':
                                    part_number = val
                                    break
                        
                        # Look for description
                        for col in df.columns:
                            if any(keyword in col.lower() for keyword in ['description', 'desc', 'name', 'item description']):
                                val = str(row_data[col]).strip()
                                if val and val != 'nan' and val != 'None':
                                    description = val
                                    break
                        
                        # Look for price
                        for col in df.columns:
                            if any(keyword in col.lower() for keyword in ['price', 'cost', 'rate', 'value', 'amount', 'rs', 'inr']):
                                try:
                                    val = str(row_data[col]).strip()
                                    if val and val != 'nan' and val != 'None':
                                        # Clean price
                                        val = re.sub(r'[₹$€£,₹\s]', '', val)
                                        val = re.sub(r'[a-zA-Z\s]', '', val)
                                        if val:
                                            price = float(val)
                                        break
                                except:
                                    continue
                        
                        # Look for quantity
                        for col in df.columns:
                            if any(keyword in col.lower() for keyword in ['qty', 'quantity', 'stock', 'available']):
                                try:
                                    val = str(row_data[col]).strip()
                                    if val and val != 'nan' and val != 'None':
                                        quantity = int(float(val))
                                        break
                                except:
                                    continue
                        
                        # Look for min stock
                        for col in df.columns:
                            if any(keyword in col.lower() for keyword in ['min', 'maintain', 'reorder', 'to maintain']):
                                try:
                                    val = str(row_data[col]).strip()
                                    if val and val != 'nan' and val != 'None':
                                        min_stock = int(float(val))
                                        break
                                except:
                                    continue
                        
                        # Skip empty rows
                        if not part_number and not description:
                            continue
                        
                        # Categorize based on description
                        desc_lower = description.lower()
                        if any(keyword in desc_lower for keyword in ['pneumatic', 'cylinder', 'valve', 'festo', 'smc', 'connector', 'fitting']):
                            category = 'Pneumatic Components'
                        elif any(keyword in desc_lower for keyword in ['contactor', 'mcb', 'mccb', 'relay', 'electrical', 'switch']):
                            category = 'Electrical Components'
                        elif any(keyword in desc_lower for keyword in ['motor', 'servo', 'drive', 'mitsubishi', 'gear', 'gearbox']):
                            category = 'Motors & Drives'
                        elif any(keyword in desc_lower for keyword in ['cable', 'wire', 'connector', 'lapp', 'phoenix']):
                            category = 'Cables & Connectors'
                        elif any(keyword in desc_lower for keyword in ['sensor', 'sick', 'omron', 'reed switch', 'proximity']):
                            category = 'Sensors & Instrumentation'
                        elif any(keyword in desc_lower for keyword in ['bearing', 'sprocket', 'chain', 'linear', 'rail']):
                            category = 'Mechanical Components'
                        elif any(keyword in desc_lower for keyword in ['heater', 'heating', 'ceramic', 'ceramix']):
                            category = 'Heating Elements'
                        elif any(keyword in desc_lower for keyword in ['plc', 'control', 'programmable', 'fx2n', 'fx3u']):
                            category = 'PLC & Control Systems'
                        else:
                            category = 'Other Components'
                        
                        # Insert into Silver
                        conn.execute('''
                            INSERT INTO silver_inventory_items 
                            (part_number, description, brand, category, unit_price_inr, 
                             quantity, min_stock, source_file, source_sheet, 
                             ai_confidence, validation_status)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            part_number, description, brand, category, price,
                            quantity, min_stock, Path(source_file).name, sheet_name,
                            'high', 'validated'
                        ))
                        
                        processed_count += 1
                        
                    except Exception as e:
                        continue
                        
        except Exception as e:
            continue
    
    conn.commit()
    print(f'Populated Silver database: {processed_count} items processed')
    
    # Show final stats
    total_items = conn.execute('SELECT COUNT(*) FROM silver_inventory_items').fetchone()[0]
    items_with_prices = conn.execute('SELECT COUNT(*) FROM silver_inventory_items WHERE unit_price_inr > 0').fetchone()[0]
    items_with_brands = conn.execute('SELECT COUNT(*) FROM silver_inventory_items WHERE brand != "Unknown"').fetchone()[0]
    
    print(f'Total items: {total_items:,}')
    print(f'Items with prices: {items_with_prices:,}')
    print(f'Items with brands: {items_with_brands:,}')
    
    conn.close()

if __name__ == "__main__":
    populate_silver()
