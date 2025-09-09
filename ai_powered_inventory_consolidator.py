#!/usr/bin/env python3
"""
AI-Powered Machinecraft Inventory Consolidator
Uses OpenAI API to validate and correct part numbers, descriptions, brands, and prices
"""

import pandas as pd
import os
import glob
import re
import json
import requests
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

class AIPoweredInventoryConsolidator:
    def __init__(self, base_path, openai_api_key):
        self.base_path = Path(base_path)
        self.openai_api_key = openai_api_key
        self.all_items = []
        self.processed_files = []
        self.errors = []
        self.skipped_files = []
        
    def call_openai_api(self, prompt, max_tokens=1000):
        """Call OpenAI API for data validation and correction"""
        try:
            headers = {
                'Authorization': f'Bearer {self.openai_api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'model': 'gpt-4',
                'messages': [
                    {
                        'role': 'system',
                        'content': 'You are an expert in industrial equipment and inventory management. You specialize in identifying and categorizing machine components, electrical parts, pneumatic components, and industrial equipment. Always provide accurate, professional responses.'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'max_tokens': max_tokens,
                'temperature': 0.1
            }
            
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content'].strip()
            else:
                print(f"OpenAI API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error calling OpenAI API: {str(e)}")
            return None
    
    def validate_item_data(self, part_number, description, brand, price):
        """Use AI to validate and correct item data"""
        prompt = f"""
        Please analyze and correct this industrial inventory item data:

        Part Number: {part_number}
        Description: {description}
        Brand: {brand}
        Price: {price}

        Please provide a JSON response with the following structure:
        {{
            "part_number": "corrected part number if needed",
            "description": "corrected and standardized description",
            "brand": "corrected brand name (use standard brand names like Mitsubishi, FESTO, SMC, Eaton, etc.)",
            "price": corrected_price_as_number,
            "category": "appropriate category from: PLC & Control Systems, Motors & Drives, Pneumatic Components, Electrical Components, Sensors & Instrumentation, Mechanical Components, Heating Elements, Enclosures & Cabinets, Cables & Connectors, Fasteners & Hardware, Tools & Equipment, Hydraulic Components, Safety Equipment",
            "confidence": "high/medium/low",
            "notes": "any important notes about this item"
        }}

        Rules:
        1. If part number looks like a model number (e.g., FX2N-16EX-ES/UL), keep it as is
        2. If description is unclear, try to infer from part number patterns
        3. Use standard brand names (Mitsubishi, FESTO, SMC, Eaton, Omron, SICK, Phoenix, etc.)
        4. If price is 0 or missing, try to infer if it's a high-value or low-value item
        5. Categorize based on the item's actual function, not just keywords
        """
        
        result = self.call_openai_api(prompt)
        if result:
            try:
                # Extract JSON from response
                json_start = result.find('{')
                json_end = result.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    json_str = result[json_start:json_end]
                    return json.loads(json_str)
            except:
                pass
        
        # Fallback if AI fails
        return {
            "part_number": part_number,
            "description": description,
            "brand": brand,
            "price": price,
            "category": "Uncategorized",
            "confidence": "low",
            "notes": "AI validation failed"
        }
    
    def find_all_excel_files(self):
        """Find ALL Excel files recursively in all directories and subdirectories"""
        excel_files = []
        
        patterns = [
            "**/*.xlsx",
            "**/*.xls",
            "**/*.XLSX",
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
            'lathe': 'Lathe'
        }
        
        for key, brand in brand_mappings.items():
            if key in filename or key in filepath:
                return brand
        
        return "Unknown Brand"
    
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
            'inventory_template',
            'master_inventory',
            'professional_master'
        ]
        
        for pattern in skip_patterns:
            if pattern in filename:
                return True
        
        return False
    
    def process_excel_file(self, file_path):
        """Enhanced Excel file processing with AI validation"""
        try:
            if self.should_skip_file(file_path):
                self.skipped_files.append(file_path)
                return
            
            print(f"Processing: {file_path}")
            
            excel_file = pd.ExcelFile(file_path)
            brand = self.extract_brand_from_filename(file_path)
            
            for sheet_name in excel_file.sheet_names:
                try:
                    # Try different ways to read the sheet
                    df = None
                    
                    for skip_rows in [0, 1, 2, 3]:
                        try:
                            df = pd.read_excel(file_path, sheet_name=sheet_name, skiprows=skip_rows)
                            if not df.empty and len(df.columns) > 2:
                                break
                        except:
                            continue
                    
                    if df is None or df.empty:
                        continue
                    
                    # Enhanced column mappings
                    column_mappings = {
                        'part_number': ['part number', 'part no', 'part_no', 'model', 'model no', 'model_no', 'item', 'item no', 'item_no', 'code', 'sku', 'part', 'component', 'ref', 'reference', 'part code', 'item code'],
                        'description': ['description', 'desc', 'name', 'product', 'item description', 'item_desc', 'specification', 'spec', 'details', 'remarks', 'notes', 'product name', 'item name'],
                        'price': ['price', 'cost', 'rate', 'unit price', 'unit_price', 'value', 'amount', 'rs', 'inr', 'rupees', 'total', 'unit cost', 'selling price', 'list price'],
                        'quantity': ['quantity', 'qty', 'stock', 'available', 'in stock', 'count', 'pieces', 'nos', 'units', 'available qty', 'stock qty'],
                        'min_stock': ['min stock', 'min_stock', 'minimum', 'reorder level', 'reorder_level', 'reorder point', 'safety stock', 'min qty']
                    }
                    
                    # Find matching columns with fuzzy matching
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
                                        if re.match(r'^[A-Z0-9\-_\./]+$', val) and len(val) > 3:
                                            part_number = val
                                            break
                                        # Check if it looks like a description
                                        elif len(val) > 10 and any(char.isalpha() for char in val):
                                            description = val
                                            break
                            
                            # Skip if still no useful data
                            if not part_number and not description:
                                continue
                            
                            # Use AI to validate and correct the data
                            ai_result = self.validate_item_data(part_number, description, brand, price)
                            
                            # Create item record with AI-validated data
                            item = {
                                'part_number': ai_result.get('part_number', part_number),
                                'description': ai_result.get('description', description),
                                'brand': ai_result.get('brand', brand),
                                'price_inr': ai_result.get('price', price),
                                'quantity': quantity,
                                'min_stock': min_stock,
                                'category': ai_result.get('category', 'Uncategorized'),
                                'confidence': ai_result.get('confidence', 'low'),
                                'notes': ai_result.get('notes', ''),
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
        """Enhanced deduplication with AI-validated data"""
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
    
    def create_ai_validated_excel(self, output_file):
        """Create AI-validated Excel file"""
        print("Creating AI-validated Excel file...")
        
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
            # Main inventory sheet
            main_df = df[['part_number', 'description', 'brand', 'category', 'price_inr', 'quantity', 'min_stock', 'total_value', 'stock_status', 'price_range', 'confidence', 'source_file']].copy()
            main_df.columns = ['Part Number', 'Description', 'Brand', 'Category', 'Unit Price (INR)', 'Quantity', 'Min Stock', 'Total Value (INR)', 'Stock Status', 'Price Range', 'AI Confidence', 'Source File']
            
            main_df.to_excel(writer, sheet_name='AI-Validated Inventory', index=False)
            
            # High confidence items only
            high_conf_df = df[df['confidence'] == 'high'].copy()
            if not high_conf_df.empty:
                high_conf_df = high_conf_df[['part_number', 'description', 'brand', 'category', 'price_inr', 'quantity', 'total_value']].copy()
                high_conf_df.columns = ['Part Number', 'Description', 'Brand', 'Category', 'Unit Price (INR)', 'Quantity', 'Total Value (INR)']
                high_conf_df.to_excel(writer, sheet_name='High Confidence Items', index=False)
            
            # Brand-wise inventory
            for brand in sorted(df['brand'].unique()):
                brand_df = df[df['brand'] == brand].copy()
                brand_df = brand_df.sort_values('price_inr', ascending=False)
                brand_df = brand_df[['part_number', 'description', 'category', 'price_inr', 'quantity', 'total_value', 'confidence']].copy()
                brand_df.columns = ['Part Number', 'Description', 'Category', 'Unit Price (INR)', 'Quantity', 'Total Value (INR)', 'AI Confidence']
                
                # Clean brand name for sheet name
                sheet_name = brand.replace('/', '_').replace('\\', '_')[:31]
                brand_df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Category analysis
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
            
            # AI confidence analysis
            confidence_analysis = df.groupby('confidence').agg({
                'part_number': 'count',
                'price_inr': 'sum'
            }).round(2)
            confidence_analysis.columns = ['Item Count', 'Total Value (INR)']
            confidence_analysis.to_excel(writer, sheet_name='AI Confidence Analysis', index=True)
            
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
        
        print(f"AI-validated Excel file created: {output_file}")
    
    def generate_report(self):
        """Generate a comprehensive summary report"""
        print("\n" + "="*70)
        print("AI-POWERED INVENTORY CONSOLIDATION REPORT")
        print("="*70)
        print(f"Total files processed: {len(self.processed_files)}")
        print(f"Total files skipped: {len(self.skipped_files)}")
        print(f"Total items found: {len(self.all_items)}")
        print(f"Total errors: {len(self.errors)}")
        
        if self.all_items:
            df = pd.DataFrame(self.all_items)
            df = df[df['category'] != 'Uncategorized']
            
            print(f"\nCategories found: {df['category'].nunique()}")
            print(f"Brands found: {df['brand'].nunique()}")
            print(f"Total inventory value: ₹{df['price_inr'].sum():,.2f}")
            print(f"Average item price: ₹{df['price_inr'].mean():,.2f}")
            
            # AI confidence analysis
            confidence_counts = df['confidence'].value_counts()
            print(f"\nAI Confidence Analysis:")
            for conf, count in confidence_counts.items():
                print(f"  {conf}: {count} items")
            
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
            for error in self.errors[:10]:
                print(f"  - {error}")
            if len(self.errors) > 10:
                print(f"  ... and {len(self.errors) - 10} more errors")
    
    def run(self):
        """Main execution method"""
        print("Starting AI-powered inventory consolidation...")
        
        # Find all Excel files recursively
        excel_files = self.find_all_excel_files()
        print(f"Found {len(excel_files)} Excel files to process")
        
        # Process each file
        for file_path in excel_files:
            self.process_excel_file(file_path)
        
        # Deduplicate items
        self.deduplicate_items()
        
        # Create AI-validated Excel file
        output_file = self.base_path / "AI_Validated_Master_Inventory.xlsx"
        self.create_ai_validated_excel(output_file)
        
        # Generate report
        self.generate_report()
        
        return output_file

def main():
    base_path = "/Users/rushabhdoshi/Library/CloudStorage/Box-Box/MCRAFT 2023/11 Inventory"
    openai_api_key = "your-openai-api-key-here"
    
    consolidator = AIPoweredInventoryConsolidator(base_path, openai_api_key)
    output_file = consolidator.run()
    print(f"\nAI-powered consolidation complete! Master file saved as: {output_file}")

if __name__ == "__main__":
    main()
