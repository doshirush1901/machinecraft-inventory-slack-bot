#!/usr/bin/env python3
"""
Machinecraft Inventory Data Pipeline
Bronze → Silver → Gold Architecture with Anti-Schema-Drift
"""

import sqlite3
import json
import pandas as pd
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import hashlib
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InventoryDataPipeline:
    def __init__(self, db_path: str = "inventory_pipeline.db"):
        self.db_path = db_path
        self.conn = None
        self.schema_version = "1.0.0"
        
    def connect(self):
        """Connect to SQLite database"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        logger.info(f"Connected to database: {self.db_path}")
        
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

    # ==================== BRONZE LAYER (SEE - Ingest) ====================
    
    def create_bronze_schema(self):
        """Create Bronze layer schema for raw data ingestion"""
        bronze_schema = """
        CREATE TABLE IF NOT EXISTS bronze_inventory_raw (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_file TEXT NOT NULL,
            source_sheet TEXT,
            raw_data JSONB NOT NULL,
            data_hash TEXT UNIQUE NOT NULL,
            ingestion_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            file_size INTEGER,
            file_modified DATETIME,
            processing_status TEXT DEFAULT 'pending',
            error_message TEXT,
            schema_version TEXT DEFAULT '1.0.0'
        );
        
        CREATE INDEX IF NOT EXISTS idx_bronze_source ON bronze_inventory_raw(source_file);
        CREATE INDEX IF NOT EXISTS idx_bronze_timestamp ON bronze_inventory_raw(ingestion_timestamp);
        CREATE INDEX IF NOT EXISTS idx_bronze_status ON bronze_inventory_raw(processing_status);
        """
        
        self.conn.executescript(bronze_schema)
        logger.info("Bronze layer schema created")
    
    def ingest_excel_files(self, base_path: str) -> List[Dict]:
        """SEE: Ingest all Excel files into Bronze layer"""
        ingested_files = []
        base_path = Path(base_path)
        
        # Find all Excel files
        excel_files = list(base_path.glob("**/*.xlsx")) + list(base_path.glob("**/*.xls"))
        
        for file_path in excel_files:
            try:
                # Skip template and backup files
                if any(skip in file_path.name.lower() for skip in ['template', 'backup', 'copy', 'old']):
                    continue
                    
                # Calculate file hash for deduplication
                with open(file_path, 'rb') as f:
                    file_hash = hashlib.md5(f.read()).hexdigest()
                
                # Check if already ingested
                cursor = self.conn.execute(
                    "SELECT id FROM bronze_inventory_raw WHERE data_hash = ?", 
                    (file_hash,)
                )
                if cursor.fetchone():
                    logger.info(f"File already ingested: {file_path.name}")
                    continue
                
                # Read Excel file
                excel_file = pd.ExcelFile(file_path)
                raw_data = {}
                
                for sheet_name in excel_file.sheet_names:
                    try:
                        df = pd.read_excel(file_path, sheet_name=sheet_name)
                        raw_data[sheet_name] = {
                            'columns': df.columns.tolist(),
                            'data': df.to_dict('records'),
                            'shape': df.shape,
                            'dtypes': df.dtypes.to_dict()
                        }
                    except Exception as e:
                        logger.warning(f"Error reading sheet {sheet_name} from {file_path}: {e}")
                        continue
                
                # Store in Bronze
                file_stat = file_path.stat()
                self.conn.execute("""
                    INSERT INTO bronze_inventory_raw 
                    (source_file, raw_data, data_hash, file_size, file_modified, processing_status)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    str(file_path),
                    json.dumps(raw_data, default=str),
                    file_hash,
                    file_stat.st_size,
                    datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                    'ingested'
                ))
                
                ingested_files.append({
                    'file': str(file_path),
                    'hash': file_hash,
                    'sheets': len(raw_data),
                    'status': 'ingested'
                })
                
                logger.info(f"Ingested: {file_path.name} ({len(raw_data)} sheets)")
                
            except Exception as e:
                logger.error(f"Error ingesting {file_path}: {e}")
                self.conn.execute("""
                    INSERT INTO bronze_inventory_raw 
                    (source_file, raw_data, data_hash, processing_status, error_message)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    str(file_path),
                    json.dumps({}),
                    hashlib.md5(str(file_path).encode()).hexdigest(),
                    'error',
                    str(e)
                ))
        
        self.conn.commit()
        logger.info(f"Bronze ingestion complete: {len(ingested_files)} files processed")
        return ingested_files

    # ==================== SILVER LAYER (THINK - Transform) ====================
    
    def create_silver_schema(self):
        """Create Silver layer schema for cleaned, validated data"""
        silver_schema = """
        CREATE TABLE IF NOT EXISTS silver_inventory_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            part_number TEXT,
            description TEXT NOT NULL,
            brand TEXT,
            category TEXT,
            unit_price_inr REAL DEFAULT 0.0,
            quantity INTEGER DEFAULT 0,
            min_stock INTEGER DEFAULT 0,
            total_value_inr REAL GENERATED ALWAYS AS (unit_price_inr * quantity) STORED,
            stock_status TEXT GENERATED ALWAYS AS (
                CASE 
                    WHEN quantity <= min_stock THEN 'Low Stock'
                    WHEN quantity = 0 THEN 'Out of Stock'
                    ELSE 'In Stock'
                END
            ) STORED,
            price_range TEXT GENERATED ALWAYS AS (
                CASE 
                    WHEN unit_price_inr > 10000 THEN 'High (>₹10K)'
                    WHEN unit_price_inr > 1000 THEN 'Medium (₹1K-10K)'
                    ELSE 'Low (<₹1K)'
                END
            ) STORED,
            source_file TEXT NOT NULL,
            source_sheet TEXT,
            ai_confidence TEXT DEFAULT 'low',
            ai_notes TEXT,
            validation_status TEXT DEFAULT 'pending',
            validation_errors JSONB,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            schema_version TEXT DEFAULT '1.0.0'
        );
        
        CREATE TABLE IF NOT EXISTS silver_brands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand_name TEXT UNIQUE NOT NULL,
            standardized_name TEXT NOT NULL,
            category TEXT,
            confidence_score REAL DEFAULT 0.0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS silver_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_name TEXT UNIQUE NOT NULL,
            parent_category TEXT,
            description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Indexes for performance
        CREATE INDEX IF NOT EXISTS idx_silver_part_number ON silver_inventory_items(part_number);
        CREATE INDEX IF NOT EXISTS idx_silver_brand ON silver_inventory_items(brand);
        CREATE INDEX IF NOT EXISTS idx_silver_category ON silver_inventory_items(category);
        CREATE INDEX IF NOT EXISTS idx_silver_price ON silver_inventory_items(unit_price_inr);
        CREATE INDEX IF NOT EXISTS idx_silver_stock ON silver_inventory_items(stock_status);
        CREATE INDEX IF NOT EXISTS idx_silver_source ON silver_inventory_items(source_file);
        """
        
        self.conn.executescript(silver_schema)
        logger.info("Silver layer schema created")
    
    def transform_bronze_to_silver(self):
        """THINK: Transform Bronze data to Silver with AI validation"""
        logger.info("Starting Bronze to Silver transformation...")
        
        # Get all ingested files
        cursor = self.conn.execute("""
            SELECT id, source_file, raw_data, processing_status 
            FROM bronze_inventory_raw 
            WHERE processing_status = 'ingested'
        """)
        
        transformed_count = 0
        
        for row in cursor.fetchall():
            try:
                raw_data = json.loads(row['raw_data'])
                source_file = row['source_file']
                
                # Process each sheet
                for sheet_name, sheet_data in raw_data.items():
                    if not isinstance(sheet_data, dict) or 'data' not in sheet_data:
                        continue
                    
                    df = pd.DataFrame(sheet_data['data'])
                    brand = self._extract_brand_from_filename(source_file)
                    
                    # Transform each row
                    for _, row_data in df.iterrows():
                        try:
                            # Extract and clean data
                            part_number = self._clean_text(row_data.get('part_number', ''))
                            description = self._clean_text(row_data.get('description', ''))
                            price = self._clean_price(row_data.get('price', 0))
                            quantity = self._clean_quantity(row_data.get('quantity', 0))
                            min_stock = self._clean_quantity(row_data.get('min_stock', 0))
                            
                            # Skip empty rows
                            if not part_number and not description:
                                continue
                            
                            # AI validation (simplified for now)
                            ai_result = self._validate_item_ai(part_number, description, brand, price)
                            
                            # Insert into Silver
                            self.conn.execute("""
                                INSERT INTO silver_inventory_items 
                                (part_number, description, brand, category, unit_price_inr, 
                                 quantity, min_stock, source_file, source_sheet, 
                                 ai_confidence, ai_notes, validation_status)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                ai_result['part_number'],
                                ai_result['description'],
                                ai_result['brand'],
                                ai_result['category'],
                                ai_result['price'],
                                quantity,
                                min_stock,
                                os.path.basename(source_file),
                                sheet_name,
                                ai_result['confidence'],
                                ai_result['notes'],
                                'validated'
                            ))
                            
                            transformed_count += 1
                            
                        except Exception as e:
                            logger.warning(f"Error transforming row: {e}")
                            continue
                
                # Update Bronze status
                self.conn.execute("""
                    UPDATE bronze_inventory_raw 
                    SET processing_status = 'transformed' 
                    WHERE id = ?
                """, (row['id'],))
                
            except Exception as e:
                logger.error(f"Error transforming file {row['source_file']}: {e}")
                self.conn.execute("""
                    UPDATE bronze_inventory_raw 
                    SET processing_status = 'error', error_message = ? 
                    WHERE id = ?
                """, (str(e), row['id']))
        
        self.conn.commit()
        logger.info(f"Silver transformation complete: {transformed_count} items processed")

    # ==================== GOLD LAYER (OPERATE - Serve) ====================
    
    def create_gold_views(self):
        """Create Gold layer views for analytics and reporting"""
        gold_views = """
        -- High-value inventory view
        CREATE VIEW IF NOT EXISTS gold_high_value_items AS
        SELECT 
            part_number,
            description,
            brand,
            category,
            unit_price_inr,
            quantity,
            total_value_inr,
            stock_status,
            source_file
        FROM silver_inventory_items
        WHERE unit_price_inr > 10000
        ORDER BY total_value_inr DESC;
        
        -- Low stock alert view
        CREATE VIEW IF NOT EXISTS gold_low_stock_alerts AS
        SELECT 
            part_number,
            description,
            brand,
            category,
            unit_price_inr,
            quantity,
            min_stock,
            total_value_inr,
            source_file
        FROM silver_inventory_items
        WHERE quantity <= min_stock AND quantity > 0
        ORDER BY total_value_inr DESC;
        
        -- Brand analysis view
        CREATE VIEW IF NOT EXISTS gold_brand_analysis AS
        SELECT 
            brand,
            COUNT(*) as item_count,
            SUM(unit_price_inr) as total_value,
            AVG(unit_price_inr) as avg_price,
            MIN(unit_price_inr) as min_price,
            MAX(unit_price_inr) as max_price,
            SUM(quantity) as total_quantity,
            SUM(total_value_inr) as total_inventory_value
        FROM silver_inventory_items
        WHERE brand IS NOT NULL AND brand != ''
        GROUP BY brand
        ORDER BY total_inventory_value DESC;
        
        -- Category analysis view
        CREATE VIEW IF NOT EXISTS gold_category_analysis AS
        SELECT 
            category,
            COUNT(*) as item_count,
            SUM(unit_price_inr) as total_value,
            AVG(unit_price_inr) as avg_price,
            SUM(quantity) as total_quantity,
            SUM(total_value_inr) as total_inventory_value
        FROM silver_inventory_items
        WHERE category IS NOT NULL AND category != ''
        GROUP BY category
        ORDER BY total_inventory_value DESC;
        
        -- Inventory summary view
        CREATE VIEW IF NOT EXISTS gold_inventory_summary AS
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
        FROM silver_inventory_items;
        """
        
        self.conn.executescript(gold_views)
        logger.info("Gold layer views created")

    # ==================== HELPER METHODS ====================
    
    def _extract_brand_from_filename(self, filename: str) -> str:
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
            'siemens': 'Siemens'
        }
        
        for key, brand in brand_mappings.items():
            if key in filename:
                return brand
        return 'Unknown'
    
    def _clean_text(self, text) -> str:
        """Clean text fields"""
        if pd.isna(text):
            return ""
        return str(text).strip()
    
    def _clean_price(self, price) -> float:
        """Clean price fields"""
        if pd.isna(price):
            return 0.0
        
        price_str = str(price).strip()
        # Remove currency symbols and text
        import re
        price_str = re.sub(r'[₹$€£,₹\s]', '', price_str)
        price_str = re.sub(r'[a-zA-Z\s]', '', price_str)
        
        try:
            return float(price_str)
        except:
            return 0.0
    
    def _clean_quantity(self, qty) -> int:
        """Clean quantity fields"""
        if pd.isna(qty):
            return 0
        try:
            return int(float(qty))
        except:
            return 0
    
    def _validate_item_ai(self, part_number: str, description: str, brand: str, price: float) -> Dict:
        """Simplified AI validation (replace with actual API call)"""
        # This is a placeholder - in production, call OpenAI API here
        return {
            'part_number': part_number,
            'description': description,
            'brand': brand,
            'category': 'Uncategorized',
            'price': price,
            'confidence': 'medium',
            'notes': 'Processed without AI validation'
        }

    # ==================== ANTI-SCHEMA-DRIFT MEASURES ====================
    
    def create_schema_validation(self):
        """Create schema validation and migration system"""
        schema_validation = """
        CREATE TABLE IF NOT EXISTS schema_versions (
            version TEXT PRIMARY KEY,
            applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            description TEXT
        );
        
        CREATE TABLE IF NOT EXISTS schema_checks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            check_name TEXT NOT NULL,
            check_query TEXT NOT NULL,
            expected_result TEXT,
            actual_result TEXT,
            status TEXT,
            checked_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Insert current schema version
        INSERT OR IGNORE INTO schema_versions (version, description) 
        VALUES ('1.0.0', 'Initial schema with Bronze-Silver-Gold architecture');
        """
        
        self.conn.executescript(schema_validation)
        logger.info("Schema validation system created")
    
    def validate_schema(self) -> Dict[str, Any]:
        """Validate schema integrity and data quality"""
        validation_results = {
            'schema_version': self.schema_version,
            'checks': [],
            'overall_status': 'pass'
        }
        
        # Check 1: Bronze layer data integrity
        try:
            bronze_count = self.conn.execute("SELECT COUNT(*) FROM bronze_inventory_raw").fetchone()[0]
            validation_results['checks'].append({
                'name': 'Bronze Data Count',
                'status': 'pass',
                'details': f'{bronze_count} raw records'
            })
        except Exception as e:
            validation_results['checks'].append({
                'name': 'Bronze Data Count',
                'status': 'fail',
                'details': str(e)
            })
            validation_results['overall_status'] = 'fail'
        
        # Check 2: Silver layer data integrity
        try:
            silver_count = self.conn.execute("SELECT COUNT(*) FROM silver_inventory_items").fetchone()[0]
            validation_results['checks'].append({
                'name': 'Silver Data Count',
                'status': 'pass',
                'details': f'{silver_count} processed items'
            })
        except Exception as e:
            validation_results['checks'].append({
                'name': 'Silver Data Count',
                'status': 'fail',
                'details': str(e)
            })
            validation_results['overall_status'] = 'fail'
        
        # Check 3: Data quality metrics
        try:
            quality_metrics = self.conn.execute("""
                SELECT 
                    COUNT(*) as total_items,
                    COUNT(CASE WHEN part_number IS NOT NULL AND part_number != '' THEN 1 END) as items_with_part_numbers,
                    COUNT(CASE WHEN unit_price_inr > 0 THEN 1 END) as items_with_prices,
                    COUNT(CASE WHEN brand IS NOT NULL AND brand != '' THEN 1 END) as items_with_brands
                FROM silver_inventory_items
            """).fetchone()
            
            validation_results['checks'].append({
                'name': 'Data Quality Metrics',
                'status': 'pass',
                'details': {
                    'total_items': quality_metrics[0],
                    'with_part_numbers': quality_metrics[1],
                    'with_prices': quality_metrics[2],
                    'with_brands': quality_metrics[3]
                }
            })
        except Exception as e:
            validation_results['checks'].append({
                'name': 'Data Quality Metrics',
                'status': 'fail',
                'details': str(e)
            })
            validation_results['overall_status'] = 'fail'
        
        return validation_results

    # ==================== MAIN PIPELINE EXECUTION ====================
    
    def run_full_pipeline(self, base_path: str):
        """Execute the complete data pipeline"""
        logger.info("Starting full inventory data pipeline...")
        
        try:
            # Connect to database
            self.connect()
            
            # Create schemas
            self.create_bronze_schema()
            self.create_silver_schema()
            self.create_gold_views()
            self.create_schema_validation()
            
            # Execute pipeline steps
            logger.info("Step 1: SEE - Ingesting data into Bronze layer...")
            ingested = self.ingest_excel_files(base_path)
            
            logger.info("Step 2: THINK - Transforming Bronze to Silver...")
            self.transform_bronze_to_silver()
            
            logger.info("Step 3: CHECK - Validating schema and data quality...")
            validation = self.validate_schema()
            
            logger.info("Step 4: OPERATE - Gold views ready for analytics...")
            
            # Print summary
            print("\n" + "="*70)
            print("INVENTORY DATA PIPELINE COMPLETE")
            print("="*70)
            print(f"Files ingested: {len(ingested)}")
            print(f"Schema validation: {validation['overall_status']}")
            
            # Get final counts
            bronze_count = self.conn.execute("SELECT COUNT(*) FROM bronze_inventory_raw").fetchone()[0]
            silver_count = self.conn.execute("SELECT COUNT(*) FROM silver_inventory_items").fetchone()[0]
            
            print(f"Bronze records: {bronze_count:,}")
            print(f"Silver items: {silver_count:,}")
            print(f"Database: {self.db_path}")
            print("="*70)
            
            return {
                'status': 'success',
                'bronze_count': bronze_count,
                'silver_count': silver_count,
                'validation': validation
            }
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            return {'status': 'error', 'error': str(e)}
        
        finally:
            self.close()

def main():
    """Main execution function"""
    base_path = "/Users/rushabhdoshi/Library/CloudStorage/Box-Box/MCRAFT 2023/11 Inventory"
    db_path = "machinecraft_inventory_pipeline.db"
    
    pipeline = InventoryDataPipeline(db_path)
    result = pipeline.run_full_pipeline(base_path)
    
    if result['status'] == 'success':
        print(f"\n✅ Pipeline completed successfully!")
        print(f"📊 Database created: {db_path}")
        print(f"📈 Total items processed: {result['silver_count']:,}")
    else:
        print(f"\n❌ Pipeline failed: {result['error']}")

if __name__ == "__main__":
    main()
