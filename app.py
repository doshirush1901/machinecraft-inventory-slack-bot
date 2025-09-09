from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import pandas as pd
import os
import json
from datetime import datetime
import re
import openai
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
openai.api_key = OPENAI_API_KEY

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'

db = SQLAlchemy(app)
CORS(app)

# Database Models
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    items = db.relationship('Item', backref='category', lazy=True)

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    part_number = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    brand = db.Column(db.String(100))
    list_price = db.Column(db.Float)
    net_price = db.Column(db.Float)
    minimum_stock = db.Column(db.Integer, default=0)
    actual_quantity = db.Column(db.Integer, default=0)
    location = db.Column(db.String(100))
    rack = db.Column(db.String(50))
    uom = db.Column(db.String(20))  # Unit of Measure
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Supplier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    contact_info = db.Column(db.Text)
    items = db.relationship('Item', backref='supplier', lazy=True)

# Data Import Functions
def clean_column_name(col):
    """Clean column names for database compatibility"""
    if pd.isna(col):
        return 'unnamed'
    col_str = str(col).strip()
    # Remove special characters and replace spaces with underscores
    col_str = re.sub(r'[^a-zA-Z0-9\s_]', '', col_str)
    col_str = re.sub(r'\s+', '_', col_str).lower()
    return col_str if col_str else 'unnamed'

def extract_category_from_filename(filename):
    """Extract category name from Excel filename"""
    name = os.path.splitext(os.path.basename(filename))[0]
    # Remove common suffixes
    name = re.sub(r'\s*(Stock|SORTED|NEW|OLD|Updated).*$', '', name, flags=re.IGNORECASE)
    return name.strip()

def import_excel_data(file_path):
    """Import data from Excel file"""
    try:
        # Read Excel file
        df = pd.read_excel(file_path)
        
        # Clean column names
        df.columns = [clean_column_name(col) for col in df.columns]
        
        # Extract category from filename
        category_name = extract_category_from_filename(file_path)
        
        # Get or create category
        category = Category.query.filter_by(name=category_name).first()
        if not category:
            category = Category(name=category_name, description=f"Items from {category_name}")
            db.session.add(category)
            db.session.commit()
        
        # Process rows
        items_created = 0
        for index, row in df.iterrows():
            # Skip empty rows or header rows
            if pd.isna(row.iloc[0]) or str(row.iloc[0]).strip() == '':
                continue
                
            # Try to find part number and description
            part_number = None
            description = None
            brand = None
            list_price = None
            net_price = None
            min_stock = 0
            actual_qty = 0
            location = None
            rack = None
            uom = None
            
            # Look for common column patterns
            for col in df.columns:
                col_lower = col.lower()
                cell_value = row[col]
                
                # Check if cell value is not NaN
                if pd.isna(cell_value):
                    continue
                    
                if 'part' in col_lower and 'number' in col_lower:
                    part_number = str(cell_value).strip()
                elif 'description' in col_lower:
                    description = str(cell_value).strip()
                elif 'brand' in col_lower:
                    brand = str(cell_value).strip()
                elif 'list' in col_lower and 'price' in col_lower:
                    try:
                        list_price = float(cell_value)
                    except:
                        pass
                elif 'net' in col_lower and 'price' in col_lower:
                    try:
                        net_price = float(cell_value)
                    except:
                        pass
                elif 'minimum' in col_lower and 'stock' in col_lower:
                    try:
                        min_stock = int(cell_value)
                    except:
                        pass
                elif 'actual' in col_lower and 'quantity' in col_lower:
                    try:
                        actual_qty = int(cell_value)
                    except:
                        pass
                elif 'location' in col_lower:
                    location = str(cell_value).strip()
                elif 'rack' in col_lower:
                    rack = str(cell_value).strip()
                elif 'uom' in col_lower:
                    uom = str(cell_value).strip()
            
            # If we have at least a part number or description, create item
            if part_number or description:
                # Check if item already exists
                existing_item = None
                if part_number:
                    existing_item = Item.query.filter_by(part_number=part_number).first()
                
                if not existing_item:
                    item = Item(
                        part_number=part_number or f"ITEM_{index}",
                        description=description or f"Item from {category_name}",
                        brand=brand,
                        list_price=list_price,
                        net_price=net_price,
                        minimum_stock=min_stock,
                        actual_quantity=actual_qty,
                        location=location,
                        rack=rack,
                        uom=uom,
                        category_id=category.id
                    )
                    db.session.add(item)
                    items_created += 1
        
        db.session.commit()
        return items_created
        
    except Exception as e:
        print(f"Error importing {file_path}: {str(e)}")
        return 0

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/categories')
def get_categories():
    categories = Category.query.all()
    return jsonify([{
        'id': cat.id,
        'name': cat.name,
        'description': cat.description,
        'item_count': len(cat.items)
    } for cat in categories])

@app.route('/api/items')
def get_items():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    category_id = request.args.get('category_id', type=int)
    search = request.args.get('search', '')
    
    query = Item.query
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            db.or_(
                Item.part_number.like(search_term),
                Item.description.like(search_term),
                Item.brand.like(search_term)
            )
        )
    
    items = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'items': [{
            'id': item.id,
            'part_number': item.part_number,
            'description': item.description,
            'brand': item.brand,
            'list_price': item.list_price,
            'net_price': item.net_price,
            'minimum_stock': item.minimum_stock,
            'actual_quantity': item.actual_quantity,
            'location': item.location,
            'rack': item.rack,
            'uom': item.uom,
            'category': item.category.name if item.category else None,
            'stock_status': 'Low' if item.actual_quantity <= item.minimum_stock else 'OK'
        } for item in items.items],
        'total': items.total,
        'pages': items.pages,
        'current_page': page
    })

@app.route('/api/import', methods=['POST'])
def import_data():
    """Import data from Excel files"""
    try:
        inventory_dir = os.path.dirname(os.path.abspath(__file__))
        excel_files = []
        
        # Find all Excel files
        for root, dirs, files in os.walk(inventory_dir):
            for file in files:
                if file.endswith(('.xlsx', '.xls')):
                    excel_files.append(os.path.join(root, file))
        
        total_items = 0
        for file_path in excel_files:
            items_created = import_excel_data(file_path)
            total_items += items_created
        
        return jsonify({
            'success': True,
            'message': f'Successfully imported {total_items} items from {len(excel_files)} files',
            'files_processed': len(excel_files),
            'items_created': total_items
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/items/<int:item_id>')
def get_item(item_id):
    item = Item.query.get_or_404(item_id)
    return jsonify({
        'id': item.id,
        'part_number': item.part_number,
        'description': item.description,
        'brand': item.brand,
        'list_price': item.list_price,
        'net_price': item.net_price,
        'minimum_stock': item.minimum_stock,
        'actual_quantity': item.actual_quantity,
        'location': item.location,
        'rack': item.rack,
        'uom': item.uom,
        'category': item.category.name if item.category else None
    })

@app.route('/api/items/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    item = Item.query.get_or_404(item_id)
    data = request.json
    
    item.part_number = data.get('part_number', item.part_number)
    item.description = data.get('description', item.description)
    item.brand = data.get('brand', item.brand)
    item.list_price = data.get('list_price', item.list_price)
    item.net_price = data.get('net_price', item.net_price)
    item.minimum_stock = data.get('minimum_stock', item.minimum_stock)
    item.actual_quantity = data.get('actual_quantity', item.actual_quantity)
    item.location = data.get('location', item.location)
    item.rack = data.get('rack', item.rack)
    item.uom = data.get('uom', item.uom)
    
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/stats')
def get_stats():
    total_items = Item.query.count()
    low_stock_items = Item.query.filter(Item.actual_quantity <= Item.minimum_stock).count()
    categories_count = Category.query.count()
    
    # Get top categories by item count
    categories = db.session.query(Category, db.func.count(Item.id).label('item_count'))\
        .join(Item)\
        .group_by(Category.id)\
        .order_by(db.func.count(Item.id).desc())\
        .limit(10)\
        .all()
    
    return jsonify({
        'total_items': total_items,
        'low_stock_items': low_stock_items,
        'categories_count': categories_count,
        'top_categories': [{'name': cat.name, 'count': count} for cat, count in categories]
    })

@app.route('/ai-search', methods=['POST'])
def ai_search():
    data = request.get_json() or {}
    query = data.get('query', '')
    if not query:
        return jsonify({'error': 'No query provided'}), 400
    try:
        # Try to get a structured response from OpenAI
        system_prompt = (
            "You are an expert inventory assistant for Machinecraft. "
            "Given a user query, return a JSON object with keys: 'main_item' (dict with part_number, description, price, vendor), "
            "and 'similar_items' (list of dicts with part_number, description, price, vendor). "
            "If you don't know, use null or empty string."
        )
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            max_tokens=400,
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        ai_data = response.choices[0].message.content.strip()
        try:
            import json
            ai_json = json.loads(ai_data)
            return jsonify(ai_json)
        except Exception:
            # Fallback: return as text
            return jsonify({'answer': ai_data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000) 