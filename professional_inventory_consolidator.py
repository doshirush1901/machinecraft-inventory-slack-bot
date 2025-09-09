#!/usr/bin/env python3
"""
Professional Machinecraft Inventory Consolidator
Creates a McMaster-Carr style professional inventory database
"""

import pandas as pd
import os
import glob
import re
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

class ProfessionalInventoryConsolidator:
    def __init__(self, base_path):
        self.base_path = Path(base_path)
        self.all_items = []
        self.processed_files = []
        self.errors = []
        self.skipped_files = []
        
    def find_all_excel_files(self):
        """Find ALL Excel files recursively in all directories and subdirectories"""
        excel_files = []
        
        # Use glob to find all Excel files recursively
        patterns = [
            "**/*.xlsx",
            "**/*.xls",
            "**/*.XLSX",  # Case variations
            "**/*.XLS"
        ]
        
        for pattern in patterns:
            excel_files.extend(glob.glob(str(self.base_path / pattern), recursive=True))
        
        # Remove duplicates and sort
        excel_files = list(set(excel_files))
        excel_files.sort()
        
        return excel_files
    
    def clean_price(self, price_str):
        """Enhanced price cleaning with more patterns"""
        if pd.isna(price_str) or price_str == '':
            return 0.0
        
        # Convert to string and clean
        price_str = str(price_str).strip()
        
        # Remove common currency symbols and text
        price_str = re.sub(r'[₹$€£,₹\s]', '', price_str)
        price_str = re.sub(r'[a-zA-Z\s]', '', price_str)
        
        # Handle ranges (take the higher value)
        if '-' in price_str:
            parts = price_str.split('-')
            try:
                return max(float(parts[0]), float(parts[1]))
            except:
                return 0.0
        
        # Handle parentheses (sometimes used for negative values)
        if '(' in price_str and ')' in price_str:
            price_str = price_str.replace('(', '-').replace(')', '')
        
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
        """Enhanced brand extraction from filename and path"""
        filename = Path(filename).stem.lower()
        filepath = str(filename).lower()
        
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
            'apratek': 'Apratek',
            'siemens': 'Siemens',
            'murr': 'Murr',
            'murrelektronik': 'Murr',
            'bonfiglioli': 'Bonfiglioli',
            'becker': 'Becker',
            'sunchu': 'Sunchu',
            'yyc': 'YYC',
            'hetronik': 'Hetronik',
            'flexicab': 'Flexicab',
            'hrc': 'HRC',
            'iac': 'IAC',
            'lathe': 'Lathe',
            'nlmk': 'NLMK',
            'sapt': 'SAPT',
            'foliplast': 'Foliplast',
            'nyxinc': 'Nyxinc',
            'self': 'Self Moulds',
            'plastoform': 'Plastoform',
            'arihant': 'Arihant',
            'looknorth': 'Looknorth',
            'shoda': 'Shoda',
            'supreme': 'Supreme',
            'asun': 'Asun',
            'big': 'Big Bear'
        }
        
        for key, brand in brand_mappings.items():
            if key in filename or key in filepath:
                return brand
        
        return "Unknown Brand"
    
    def categorize_item(self, part_number, description, brand):
        """Enhanced categorization with specific machine building categories"""
        part_lower = str(part_number).lower()
        desc_lower = str(description).lower()
        brand_lower = str(brand).lower()
        
        # PLC and Control Systems
        if any(keyword in part_lower for keyword in ['fx', 'plc', 'cpu', 'input', 'output', 'module', 'controller', 'fx2n', 'fx3u', 'fx5u', 'programmable']):
            return 'PLC & Control Systems'
        
        # Motors and Drives
        if any(keyword in part_lower or keyword in desc_lower for keyword in ['motor', 'servo', 'drive', 'inverter', 'vfd', 'stepper', 'ac motor', 'dc motor', 'servo motor', 'stepper motor']):
            return 'Motors & Drives'
        
        # Pneumatic Components
        if any(keyword in part_lower or keyword in desc_lower for keyword in ['cylinder', 'valve', 'pneumatic', 'festo', 'smc', 'pneumax', 'air', 'pneumatic cylinder', 'air cylinder', 'pneumatic valve']):
            return 'Pneumatic Components'
        
        # Electrical Components
        if any(keyword in part_lower or keyword in desc_lower for keyword in ['contactor', 'relay', 'mcb', 'mccb', 'fuse', 'terminal', 'cable', 'switch', 'breaker', 'starter', 'electrical', 'mcb', 'mccb']):
            return 'Electrical Components'
        
        # Sensors and Instrumentation
        if any(keyword in part_lower or keyword in desc_lower for keyword in ['sensor', 'proximity', 'photo', 'encoder', 'sick', 'omron', 'inductive', 'capacitive', 'pressure sensor', 'temperature sensor']):
            return 'Sensors & Instrumentation'
        
        # Mechanical Components
        if any(keyword in part_lower or keyword in desc_lower for keyword in ['bearing', 'gear', 'sprocket', 'chain', 'rail', 'linear', 'ball bearing', 'roller bearing', 'gearbox', 'gear box', 'linear rail']):
            return 'Mechanical Components'
        
        # Heating Elements
        if any(keyword in part_lower or keyword in desc_lower for keyword in ['heater', 'heating', 'ceramic', 'ceramix', 'heating element', 'band heater', 'cartridge heater']):
            return 'Heating Elements'
        
        # Enclosures and Cabinets
        if any(keyword in part_lower or keyword in desc_lower for keyword in ['enclosure', 'cabinet', 'box', 'nvent', 'wohner', 'panel', 'control panel', 'electrical panel']):
            return 'Enclosures & Cabinets'
        
        # Cables and Connectors
        if any(keyword in part_lower or keyword in desc_lower for keyword in ['cable', 'connector', 'lapp', 'murrelektronik', 'wire', 'cable gland', 'terminal block', 'plug', 'socket']):
            return 'Cables & Connectors'
        
        # Fasteners and Hardware
        if any(keyword in part_lower or keyword in desc_lower for keyword in ['bolt', 'nut', 'screw', 'washer', 'fastener', 'hardware', 'stud', 'rivet', 'pin']):
            return 'Fasteners & Hardware'
        
        # Tools and Equipment
        if any(keyword in part_lower or keyword in desc_lower for keyword in ['tool', 'equipment', 'gauge', 'meter', 'tester', 'caliper', 'micrometer']):
            return 'Tools & Equipment'
        
        # Hydraulic Components
        if any(keyword in part_lower or keyword in desc_lower for keyword in ['hydraulic', 'pump', 'hose', 'fitting', 'hydraulic cylinder']):
            return 'Hydraulic Components'
        
        # Safety Equipment
        if any(keyword in part_lower or keyword in desc_lower for keyword in ['safety', 'guard', 'emergency', 'stop', 'safety switch', 'emergency stop']):
            return 'Safety Equipment'
        
        # Try to categorize based on brand if description is unclear
        if brand_lower in ['mitsubishi', 'siemens', 'omron']:
            return 'PLC & Control Systems'
        elif brand_lower in ['festo', 'smc', 'pneumax']:
            return 'Pneumatic Components'
        elif brand_lower in ['eaton', 'phoenix', 'wohner']:
            return 'Electrical Components'
        elif brand_lower in ['sick', 'omron'] and 'sensor' not in desc_lower:
            return 'Sensors & Instrumentation'
        elif brand_lower in ['lapp', 'murrelektronik']:
            return 'Cables & Connectors'
        
        # If still can't categorize, try to infer from part number patterns
        if re.match(r'^[A-Z]{2,4}\d+', part_number):
            return 'Electrical Components'
        elif re.match(r'^[A-Z]{1,3}\d+[A-Z]', part_number):
            return 'Mechanical Components'
        
        return 'Uncategorized'
    
    def should_skip_file(self, file_path):
        """Check if file should be skipped based on name patterns"""
        filename = Path(file_path).name.lower()
        
        skip_patterns = [
            'template',
            'backup',
            'copy',
            'old',
            'test',
            'temp',
            'draft',
            'sample',
            'example',
            'inventory_template'
        ]
        
        for pattern in skip_patterns:
            if pattern in filename:
                return True
        
        return False
    
    def process_excel_file(self, file_path):
        """Enhanced Excel file processing with better data extraction"""
        try:
            if self.should_skip_file(file_path):
                self.skipped_files.append(file_path)
                return
            
            print(f"Processing: {file_path}")
            
            # Read all sheets
            excel_file = pd.ExcelFile(file_path)
            brand = self.extract_brand_from_filename(file_path)
            
            for sheet_name in excel_file.sheet_names:
                try:
                    # Try different ways to read the sheet
                    df = None
                    
                    # Method 1: Standard read
                    try:
                        df = pd.read_excel(file_path, sheet_name=sheet_name)
                    except:
                        pass
                    
                    # Method 2: Skip first few rows if needed
                    if df is None or df.empty:
                        try:
                            df = pd.read_excel(file_path, sheet_name=sheet_name, skiprows=1)
                        except:
                            pass
                    
                    # Method 3: Skip more rows
                    if df is None or df.empty:
                        try:
                            df = pd.read_excel(file_path, sheet_name=sheet_name, skiprows=2)
                        except:
                            pass
                    
                    # Method 4: Try with header=None
                    if df is None or df.empty:
                        try:
                            df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
                        except:
                            pass
                    
                    if df is None or df.empty:
                        continue
                    
                    # Enhanced column mappings
                    column_mappings = {
                        'part_number': ['part number', 'part no', 'part_no', 'model', 'model no', 'model_no', 'item', 'item no', 'item_no', 'code', 'sku', 'part', 'component', 'ref', 'reference'],
                        'description': ['description', 'desc', 'name', 'product', 'item description', 'item_desc', 'specification', 'spec', 'details', 'remarks', 'notes'],
                        'price': ['price', 'cost', 'rate', 'unit price', 'unit_price', 'value', 'amount', 'rs', 'inr', 'rupees', 'total', 'unit cost'],
                        'quantity': ['quantity', 'qty', 'stock', 'available', 'in stock', 'count', 'pieces', 'nos', 'units'],
                        'min_stock': ['min stock', 'min_stock', 'minimum', 'reorder level', 'reorder_level', 'reorder point', 'safety stock']
                    }
                    
                    # Find matching columns with fuzzy matching
                    found_columns = {}
                    for key, possible_names in column_mappings.items():
                        for col in df.columns:
                            col_lower = str(col).lower().strip()
                            if any(name in col_lower for name in possible_names):
                                found_columns[key] = col
                                break
                    
                    # If no columns found, try to infer from data
                    if not found_columns:
                        # Look for columns that might contain part numbers (alphanumeric patterns)
                        for col in df.columns:
                            col_lower = str(col).lower().strip()
                            if any(keyword in col_lower for keyword in ['part', 'model', 'item', 'code', 'ref']):
                                if 'part_number' not in found_columns:
                                    found_columns['part_number'] = col
                            elif any(keyword in col_lower for keyword in ['desc', 'name', 'product', 'spec']):
                                if 'description' not in found_columns:
                                    found_columns['description'] = col
                            elif any(keyword in col_lower for keyword in ['price', 'cost', 'rate', 'rs', 'inr']):
                                if 'price' not in found_columns:
                                    found_columns['price'] = col
                    
                    # Process each row
                    for index, row in df.iterrows():
                        try:
                            # Skip empty rows
                            if row.isna().all():
                                continue
                            
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
                            
                            # Try to extract from any column if main fields are empty
                            if not part_number and not description:
                                for col in df.columns:
                                    val = str(row[col]).strip()
                                    if val and val != 'nan' and len(val) > 2:
                                        # Check if it looks like a part number
                                        if re.match(r'^[A-Z0-9\-_\.]+$', val) and len(val) > 3:
                                            part_number = val
                                            break
                                        # Check if it looks like a description
                                        elif len(val) > 10 and any(char.isalpha() for char in val):
                                            description = val
                                            break
                            
                            # Skip if still no useful data
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
                                'source_sheet': sheet_name,
                                'source_path': str(file_path)
                            }
                            
                            self.all_items.append(item)
                            
                        except Exception as e:
                            self.errors.append(f"Error processing row {index} in {file_path} sheet {sheet_name}: {str(e)}")
                            continue
                
                except Exception as e:
                    self.errors.append(f"Error processing sheet {sheet_name} in {file_path}: {str(e)}")
                    continue
            
            self.processed_files.append(file_path)
            
        except Exception as e:
            self.errors.append(f"Error processing file {file_path}: {str(e)}")
    
    def deduplicate_items(self):
        """Enhanced deduplication with better matching logic"""
        print("Deduplicating items...")
        
        # Group by part number and description with fuzzy matching
        grouped = {}
        
        for item in self.all_items:
            # Create multiple keys for better matching
            keys = []
            
            # Primary key: part number + description
            if item['part_number'] and item['description']:
                keys.append(f"{item['part_number']}_{item['description']}".lower().strip())
            
            # Secondary key: just part number
            if item['part_number']:
                keys.append(f"{item['part_number']}".lower().strip())
            
            # Tertiary key: just description (for items without part numbers)
            if item['description'] and not item['part_number']:
                keys.append(f"desc_{item['description']}".lower().strip())
            
            # Add to groups
            for key in keys:
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
    
    def create_professional_excel(self, output_file):
        """Create a professional McMaster-Carr style Excel file"""
        print("Creating professional Excel file...")
        
        # Convert to DataFrame
        df = pd.DataFrame(self.all_items)
        
        # Remove uncategorized items
        df = df[df['category'] != 'Uncategorized']
        
        # Sort by brand, then by price (highest to lowest) within each brand
        df = df.sort_values(['brand', 'price_inr'], ascending=[True, False])
        
        # Add calculated columns
        df['total_value'] = df['price_inr'] * df['quantity']
        df['stock_status'] = df.apply(lambda x: 'Low Stock' if x['quantity'] <= x['min_stock'] else 'In Stock', axis=1)
        df['price_range'] = df['price_inr'].apply(lambda x: 
            'High (>₹10K)' if x > 10000 else 
            'Medium (₹1K-10K)' if x > 1000 else 
            'Low (<₹1K)')
        
        # Create Excel writer with multiple sheets
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Main inventory sheet with professional formatting
            main_df = df[['part_number', 'description', 'brand', 'category', 'price_inr', 'quantity', 'min_stock', 'total_value', 'stock_status', 'price_range', 'source_file']].copy()
            main_df.columns = ['Part Number', 'Description', 'Brand', 'Category', 'Unit Price (INR)', 'Quantity', 'Min Stock', 'Total Value (INR)', 'Stock Status', 'Price Range', 'Source File']
            
            main_df.to_excel(writer, sheet_name='Master Inventory', index=False)
            
            # Brand-wise inventory (McMaster style)
            for brand in sorted(df['brand'].unique()):
                brand_df = df[df['brand'] == brand].copy()
                brand_df = brand_df.sort_values('price_inr', ascending=False)
                brand_df = brand_df[['part_number', 'description', 'category', 'price_inr', 'quantity', 'total_value', 'stock_status']].copy()
                brand_df.columns = ['Part Number', 'Description', 'Category', 'Unit Price (INR)', 'Quantity', 'Total Value (INR)', 'Stock Status']
                
                # Clean brand name for sheet name
                sheet_name = brand.replace('/', '_').replace('\\', '_')[:31]  # Excel sheet name limit
                brand_df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Category summary with formulas
            category_summary = df.groupby('category').agg({
                'part_number': 'count',
                'price_inr': ['sum', 'mean', 'min', 'max'],
                'quantity': 'sum',
                'total_value': 'sum'
            }).round(2)
            category_summary.columns = ['Item Count', 'Total Value (INR)', 'Avg Price (INR)', 'Min Price (INR)', 'Max Price (INR)', 'Total Quantity', 'Total Inventory Value (INR)']
            category_summary.to_excel(writer, sheet_name='Category Analysis', index=True)
            
            # Brand analysis
            brand_analysis = df.groupby('brand').agg({
                'part_number': 'count',
                'price_inr': ['sum', 'mean', 'min', 'max'],
                'quantity': 'sum',
                'total_value': 'sum'
            }).round(2)
            brand_analysis.columns = ['Item Count', 'Total Value (INR)', 'Avg Price (INR)', 'Min Price (INR)', 'Max Price (INR)', 'Total Quantity', 'Total Inventory Value (INR)']
            brand_analysis = brand_analysis.sort_values('Total Inventory Value (INR)', ascending=False)
            brand_analysis.to_excel(writer, sheet_name='Brand Analysis', index=True)
            
            # Low stock alert
            low_stock = df[df['quantity'] <= df['min_stock']].copy()
            low_stock = low_stock.sort_values(['brand', 'price_inr'], ascending=[True, False])
            low_stock = low_stock[['part_number', 'description', 'brand', 'category', 'price_inr', 'quantity', 'min_stock', 'total_value']].copy()
            low_stock.columns = ['Part Number', 'Description', 'Brand', 'Category', 'Unit Price (INR)', 'Current Stock', 'Min Required', 'Total Value (INR)']
            low_stock.to_excel(writer, sheet_name='Low Stock Alert', index=False)
            
            # High value items
            high_value = df[df['price_inr'] > 10000].copy()
            high_value = high_value.sort_values(['brand', 'price_inr'], ascending=[True, False])
            high_value = high_value[['part_number', 'description', 'brand', 'category', 'price_inr', 'quantity', 'total_value']].copy()
            high_value.columns = ['Part Number', 'Description', 'Brand', 'Category', 'Unit Price (INR)', 'Quantity', 'Total Value (INR)']
            high_value.to_excel(writer, sheet_name='High Value Items', index=False)
            
            # Price analysis
            price_analysis = df.groupby('price_range').agg({
                'part_number': 'count',
                'price_inr': 'sum',
                'quantity': 'sum'
            }).round(2)
            price_analysis.columns = ['Item Count', 'Total Value (INR)', 'Total Quantity']
            price_analysis.to_excel(writer, sheet_name='Price Analysis', index=True)
            
            # Executive summary
            summary_data = {
                'Metric': [
                    'Total Items',
                    'Total Brands',
                    'Total Categories',
                    'Total Inventory Value (INR)',
                    'Average Item Price (INR)',
                    'Items in Stock',
                    'Low Stock Items',
                    'High Value Items (>₹10K)',
                    'Most Expensive Item',
                    'Most Common Brand'
                ],
                'Value': [
                    len(df),
                    df['brand'].nunique(),
                    df['category'].nunique(),
                    f"₹{df['total_value'].sum():,.2f}",
                    f"₹{df['price_inr'].mean():,.2f}",
                    len(df[df['quantity'] > 0]),
                    len(df[df['quantity'] <= df['min_stock']]),
                    len(df[df['price_inr'] > 10000]),
                    df.loc[df['price_inr'].idxmax(), 'part_number'] if len(df) > 0 else 'N/A',
                    df['brand'].value_counts().index[0] if len(df) > 0 else 'N/A'
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Executive Summary', index=False)
        
        print(f"Professional Excel file created: {output_file}")
    
    def generate_report(self):
        """Generate a comprehensive summary report"""
        print("\n" + "="*70)
        print("PROFESSIONAL INVENTORY CONSOLIDATION REPORT")
        print("="*70)
        print(f"Total files processed: {len(self.processed_files)}")
        print(f"Total files skipped: {len(self.skipped_files)}")
        print(f"Total items found: {len(self.all_items)}")
        print(f"Total errors: {len(self.errors)}")
        
        if self.all_items:
            df = pd.DataFrame(self.all_items)
            # Remove uncategorized items from report
            df = df[df['category'] != 'Uncategorized']
            
            print(f"\nCategories found: {df['category'].nunique()}")
            print(f"Brands found: {df['brand'].nunique()}")
            print(f"Total inventory value: ₹{df['price_inr'].sum():,.2f}")
            print(f"Average item price: ₹{df['price_inr'].mean():,.2f}")
            
            print("\nTop 15 Categories by Item Count:")
            category_counts = df['category'].value_counts().head(15)
            for category, count in category_counts.items():
                print(f"  {category}: {count} items")
            
            print("\nTop 15 Brands by Item Count:")
            brand_counts = df['brand'].value_counts().head(15)
            for brand, count in brand_counts.items():
                print(f"  {brand}: {count} items")
            
            print("\nTop 10 Brands by Total Value:")
            brand_values = df.groupby('brand')['price_inr'].sum().sort_values(ascending=False).head(10)
            for brand, value in brand_values.items():
                print(f"  {brand}: ₹{value:,.2f}")
        
        if self.errors:
            print(f"\nErrors encountered ({len(self.errors)}):")
            for error in self.errors[:10]:  # Show first 10 errors
                print(f"  - {error}")
            if len(self.errors) > 10:
                print(f"  ... and {len(self.errors) - 10} more errors")
    
    def run(self):
        """Main execution method"""
        print("Starting professional inventory consolidation...")
        
        # Find all Excel files recursively
        excel_files = self.find_all_excel_files()
        print(f"Found {len(excel_files)} Excel files to process")
        
        # Process each file
        for file_path in excel_files:
            self.process_excel_file(file_path)
        
        # Deduplicate items
        self.deduplicate_items()
        
        # Create professional Excel file
        output_file = self.base_path / "Professional_Master_Inventory.xlsx"
        self.create_professional_excel(output_file)
        
        # Generate report
        self.generate_report()
        
        return output_file

def main():
    base_path = "/Users/rushabhdoshi/Library/CloudStorage/Box-Box/MCRAFT 2023/11 Inventory"
    consolidator = ProfessionalInventoryConsolidator(base_path)
    output_file = consolidator.run()
    print(f"\nProfessional consolidation complete! Master file saved as: {output_file}")

if __name__ == "__main__":
    main()
