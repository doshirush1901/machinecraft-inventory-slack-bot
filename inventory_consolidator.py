#!/usr/bin/env python3
"""
Machinecraft Inventory Consolidator
Consolidates all Excel inventory files into a single master file with deduplication
"""

import pandas as pd
import os
import glob
import re
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

class InventoryConsolidator:
    def __init__(self, base_path):
        self.base_path = Path(base_path)
        self.all_items = []
        self.processed_files = []
        self.errors = []
        
    def find_excel_files(self):
        """Find all Excel files in the directory and subdirectories"""
        excel_files = []
        
        # Main directory Excel files
        excel_files.extend(glob.glob(str(self.base_path / "*.xlsx")))
        excel_files.extend(glob.glob(str(self.base_path / "*.xls")))
        
        # Subdirectories
        subdirs = ['Catalog', 'Material Incoming File 24-25', 'Price list', 'RFQ Sheet']
        for subdir in subdirs:
            subdir_path = self.base_path / subdir
            if subdir_path.exists():
                excel_files.extend(glob.glob(str(subdir_path / "*.xlsx")))
                excel_files.extend(glob.glob(str(subdir_path / "*.xls")))
        
        # HEATER STOCK NEW subdirectory
        heater_path = self.base_path / "HEATER STOCK NEW"
        if heater_path.exists():
            excel_files.extend(glob.glob(str(heater_path / "*.xlsx")))
            excel_files.extend(glob.glob(str(heater_path / "*.xls")))
        
        return excel_files
    
    def clean_price(self, price_str):
        """Clean and convert price to float"""
        if pd.isna(price_str) or price_str == '':
            return 0.0
        
        # Convert to string and clean
        price_str = str(price_str).strip()
        
        # Remove common currency symbols and text
        price_str = re.sub(r'[₹$€£,₹]', '', price_str)
        price_str = re.sub(r'[a-zA-Z\s]', '', price_str)
        
        # Handle ranges (take the higher value)
        if '-' in price_str:
            parts = price_str.split('-')
            try:
                return max(float(parts[0]), float(parts[1]))
            except:
                return 0.0
        
        try:
            return float(price_str)
        except:
            return 0.0
    
    def clean_text(self, text):
        """Clean text fields"""
        if pd.isna(text):
            return ""
        return str(text).strip()
    
    def extract_brand_from_filename(self, filename):
        """Extract brand name from filename"""
        filename = Path(filename).stem.lower()
        
        brand_mappings = {
            'mitsubishi': 'Mitsubishi',
            'festo': 'FESTO',
            'smc': 'SMC',
            'eaton': 'Eaton',
            'omron': 'Omron',
            'sick': 'SICK',
            'phoenix': 'Phoenix',
            'pneumax': 'Pneumax',
            'unison': 'Unison',
            'trinity': 'Trinity',
            'teknic': 'Teknic',
            'lapp': 'LAPP',
            'bearing': 'Bearing',
            'cylinder': 'Cylinder',
            'gear': 'Gearbox',
            'heater': 'Heater',
            'linear': 'Linear',
            'sprocket': 'Sprocket',
            'ceramix': 'Ceramix',
            'crydom': 'Crydom',
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
            'apratek': 'Apratek'
        }
        
        for key, brand in brand_mappings.items():
            if key in filename:
                return brand
        
        return "Other"
    
    def categorize_item(self, part_number, description, brand):
        """Categorize item based on part number, description, and brand"""
        part_lower = str(part_number).lower()
        desc_lower = str(description).lower()
        brand_lower = str(brand).lower()
        
        # PLC and Control Systems
        if any(keyword in part_lower for keyword in ['fx', 'plc', 'cpu', 'input', 'output', 'module', 'controller']):
            return 'PLC & Control Systems'
        
        # Motors and Drives
        if any(keyword in part_lower or keyword in desc_lower for keyword in ['motor', 'servo', 'drive', 'inverter', 'vfd']):
            return 'Motors & Drives'
        
        # Pneumatic Components
        if any(keyword in part_lower or keyword in desc_lower for keyword in ['cylinder', 'valve', 'pneumatic', 'festo', 'smc', 'pneumax']):
            return 'Pneumatic Components'
        
        # Electrical Components
        if any(keyword in part_lower or keyword in desc_lower for keyword in ['contactor', 'relay', 'mcb', 'mccb', 'fuse', 'terminal', 'cable']):
            return 'Electrical Components'
        
        # Sensors
        if any(keyword in part_lower or keyword in desc_lower for keyword in ['sensor', 'proximity', 'photo', 'encoder', 'sick', 'omron']):
            return 'Sensors'
        
        # Mechanical Components
        if any(keyword in part_lower or keyword in desc_lower for keyword in ['bearing', 'gear', 'sprocket', 'chain', 'rail', 'linear']):
            return 'Mechanical Components'
        
        # Heating Elements
        if any(keyword in part_lower or keyword in desc_lower for keyword in ['heater', 'heating', 'ceramic', 'ceramix']):
            return 'Heating Elements'
        
        # Enclosures and Cabinets
        if any(keyword in part_lower or keyword in desc_lower for keyword in ['enclosure', 'cabinet', 'box', 'nvent', 'wohner']):
            return 'Enclosures & Cabinets'
        
        # Cables and Connectors
        if any(keyword in part_lower or keyword in desc_lower for keyword in ['cable', 'connector', 'lapp', 'murrelektronik']):
            return 'Cables & Connectors'
        
        return 'Other Components'
    
    def process_excel_file(self, file_path):
        """Process a single Excel file and extract inventory data"""
        try:
            print(f"Processing: {file_path}")
            
            # Read all sheets
            excel_file = pd.ExcelFile(file_path)
            brand = self.extract_brand_from_filename(file_path)
            
            for sheet_name in excel_file.sheet_names:
                try:
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                    
                    # Skip empty sheets
                    if df.empty:
                        continue
                    
                    # Common column mappings
                    column_mappings = {
                        'part_number': ['part number', 'part no', 'part_no', 'model', 'model no', 'model_no', 'item', 'item no', 'item_no', 'code', 'sku'],
                        'description': ['description', 'desc', 'name', 'product', 'item description', 'item_desc'],
                        'price': ['price', 'cost', 'rate', 'unit price', 'unit_price', 'value', 'amount'],
                        'quantity': ['quantity', 'qty', 'stock', 'available', 'in stock'],
                        'min_stock': ['min stock', 'min_stock', 'minimum', 'reorder level', 'reorder_level']
                    }
                    
                    # Find matching columns
                    found_columns = {}
                    for key, possible_names in column_mappings.items():
                        for col in df.columns:
                            col_lower = str(col).lower().strip()
                            if any(name in col_lower for name in possible_names):
                                found_columns[key] = col
                                break
                    
                    # Process each row
                    for index, row in df.iterrows():
                        try:
                            # Extract data
                            part_number = ""
                            description = ""
                            price = 0.0
                            quantity = 0
                            min_stock = 0
                            
                            if 'part_number' in found_columns:
                                part_number = self.clean_text(row[found_columns['part_number']])
                            
                            if 'description' in found_columns:
                                description = self.clean_text(row[found_columns['description']])
                            
                            if 'price' in found_columns:
                                price = self.clean_price(row[found_columns['price']])
                            
                            if 'quantity' in found_columns:
                                try:
                                    qty_val = row[found_columns['quantity']]
                                    quantity = int(float(qty_val)) if not pd.isna(qty_val) else 0
                                except:
                                    quantity = 0
                            
                            if 'min_stock' in found_columns:
                                try:
                                    min_val = row[found_columns['min_stock']]
                                    min_stock = int(float(min_val)) if not pd.isna(min_val) else 0
                                except:
                                    min_stock = 0
                            
                            # Skip if no part number or description
                            if not part_number and not description:
                                continue
                            
                            # Create item record
                            item = {
                                'part_number': part_number,
                                'description': description,
                                'brand': brand,
                                'price_inr': price,
                                'quantity': quantity,
                                'min_stock': min_stock,
                                'category': self.categorize_item(part_number, description, brand),
                                'source_file': os.path.basename(file_path),
                                'source_sheet': sheet_name
                            }
                            
                            self.all_items.append(item)
                            
                        except Exception as e:
                            self.errors.append(f"Error processing row {index} in {file_path}: {str(e)}")
                            continue
                
                except Exception as e:
                    self.errors.append(f"Error processing sheet {sheet_name} in {file_path}: {str(e)}")
                    continue
            
            self.processed_files.append(file_path)
            
        except Exception as e:
            self.errors.append(f"Error processing file {file_path}: {str(e)}")
    
    def deduplicate_items(self):
        """Remove duplicates, keeping the item with highest price"""
        print("Deduplicating items...")
        
        # Group by part number and description
        grouped = {}
        
        for item in self.all_items:
            # Create a key for grouping (part number + description)
            key = f"{item['part_number']}_{item['description']}".lower().strip()
            
            if key not in grouped:
                grouped[key] = []
            
            grouped[key].append(item)
        
        # Keep only the item with highest price in each group
        deduplicated = []
        for key, items in grouped.items():
            if len(items) == 1:
                deduplicated.append(items[0])
            else:
                # Sort by price (descending) and take the first one
                items.sort(key=lambda x: x['price_inr'], reverse=True)
                deduplicated.append(items[0])
        
        self.all_items = deduplicated
        print(f"After deduplication: {len(self.all_items)} items")
    
    def create_master_excel(self, output_file):
        """Create the master Excel file with all consolidated data"""
        print("Creating master Excel file...")
        
        # Convert to DataFrame
        df = pd.DataFrame(self.all_items)
        
        # Sort by category, then brand, then part number
        df = df.sort_values(['category', 'brand', 'part_number'])
        
        # Create Excel writer with multiple sheets
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Main consolidated sheet
            df.to_excel(writer, sheet_name='Master Inventory', index=False)
            
            # Summary by category
            category_summary = df.groupby('category').agg({
                'part_number': 'count',
                'price_inr': ['sum', 'mean'],
                'quantity': 'sum'
            }).round(2)
            category_summary.columns = ['Item Count', 'Total Value (INR)', 'Avg Price (INR)', 'Total Quantity']
            category_summary.to_excel(writer, sheet_name='Category Summary')
            
            # Summary by brand
            brand_summary = df.groupby('brand').agg({
                'part_number': 'count',
                'price_inr': ['sum', 'mean'],
                'quantity': 'sum'
            }).round(2)
            brand_summary.columns = ['Item Count', 'Total Value (INR)', 'Avg Price (INR)', 'Total Quantity']
            brand_summary.to_excel(writer, sheet_name='Brand Summary')
            
            # Low stock items
            low_stock = df[df['quantity'] <= df['min_stock']]
            low_stock.to_excel(writer, sheet_name='Low Stock Items', index=False)
            
            # High value items (> ₹10,000)
            high_value = df[df['price_inr'] > 10000]
            high_value.to_excel(writer, sheet_name='High Value Items', index=False)
        
        print(f"Master Excel file created: {output_file}")
    
    def generate_report(self):
        """Generate a summary report"""
        print("\n" + "="*50)
        print("INVENTORY CONSOLIDATION REPORT")
        print("="*50)
        print(f"Total files processed: {len(self.processed_files)}")
        print(f"Total items found: {len(self.all_items)}")
        print(f"Total errors: {len(self.errors)}")
        
        if self.all_items:
            df = pd.DataFrame(self.all_items)
            print(f"\nCategories found: {df['category'].nunique()}")
            print(f"Brands found: {df['brand'].nunique()}")
            print(f"Total inventory value: ₹{df['price_inr'].sum():,.2f}")
            print(f"Average item price: ₹{df['price_inr'].mean():,.2f}")
            
            print("\nTop 10 Categories by Item Count:")
            category_counts = df['category'].value_counts().head(10)
            for category, count in category_counts.items():
                print(f"  {category}: {count} items")
            
            print("\nTop 10 Brands by Item Count:")
            brand_counts = df['brand'].value_counts().head(10)
            for brand, count in brand_counts.items():
                print(f"  {brand}: {count} items")
        
        if self.errors:
            print(f"\nErrors encountered ({len(self.errors)}):")
            for error in self.errors[:10]:  # Show first 10 errors
                print(f"  - {error}")
            if len(self.errors) > 10:
                print(f"  ... and {len(self.errors) - 10} more errors")
    
    def run(self):
        """Main execution method"""
        print("Starting inventory consolidation...")
        
        # Find all Excel files
        excel_files = self.find_excel_files()
        print(f"Found {len(excel_files)} Excel files to process")
        
        # Process each file
        for file_path in excel_files:
            self.process_excel_file(file_path)
        
        # Deduplicate items
        self.deduplicate_items()
        
        # Create master Excel file
        output_file = self.base_path / "Master_Inventory_Consolidated.xlsx"
        self.create_master_excel(output_file)
        
        # Generate report
        self.generate_report()
        
        return output_file

def main():
    base_path = "/Users/rushabhdoshi/Library/CloudStorage/Box-Box/MCRAFT 2023/11 Inventory"
    consolidator = InventoryConsolidator(base_path)
    output_file = consolidator.run()
    print(f"\nConsolidation complete! Master file saved as: {output_file}")

if __name__ == "__main__":
    main()
