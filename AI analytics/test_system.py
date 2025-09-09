#!/usr/bin/env python3
"""
Test Script for Machinecraft Inventory System
This script tests various components of the inventory management system.
"""

import requests
import json
import time
import sys
from pathlib import Path

def test_flask_server():
    """Test if Flask server is running and responding"""
    print("🔍 Testing Flask Server...")
    
    try:
        # Test basic connectivity
        response = requests.get('http://localhost:5000/api/stats', timeout=5)
        if response.status_code == 200:
            print("✅ Flask server is running and responding")
            stats = response.json()
            print(f"   - Total items: {stats.get('total_items', 0)}")
            print(f"   - Categories: {stats.get('categories_count', 0)}")
            return True
        else:
            print(f"❌ Server responded with status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Flask server. Is it running?")
        print("   Run: python3 app.py")
        return False
    except Exception as e:
        print(f"❌ Error testing server: {e}")
        return False

def test_data_import():
    """Test data import functionality"""
    print("\n📥 Testing Data Import...")
    
    try:
        response = requests.post('http://localhost:5000/api/import', timeout=30)
        if response.status_code == 200:
            result = response.json()
            print("✅ Data import successful")
            print(f"   - Files processed: {result.get('files_processed', 0)}")
            print(f"   - Items created: {result.get('items_created', 0)}")
            return True
        else:
            print(f"❌ Import failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error during import: {e}")
        return False

def test_search_functionality():
    """Test search functionality"""
    print("\n🔍 Testing Search Functionality...")
    
    try:
        # Test basic search
        response = requests.get('http://localhost:5000/api/items?search=mitsubishi', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Search working - found {len(data.get('items', []))} items")
            return True
        else:
            print(f"❌ Search failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing search: {e}")
        return False

def test_categories():
    """Test category functionality"""
    print("\n📂 Testing Categories...")
    
    try:
        response = requests.get('http://localhost:5000/api/categories', timeout=5)
        if response.status_code == 200:
            categories = response.json()
            print(f"✅ Categories loaded - {len(categories)} categories found")
            for cat in categories[:5]:  # Show first 5 categories
                print(f"   - {cat.get('name', 'Unknown')}: {cat.get('item_count', 0)} items")
            return True
        else:
            print(f"❌ Categories failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing categories: {e}")
        return False

def test_html_dashboard():
    """Test if HTML dashboard files exist"""
    print("\n🌐 Testing HTML Dashboard...")
    
    dashboard_files = [
        "AI analytics/Simple_Inventory_Dashboard.html",
        "AI analytics/Inventory_Dashboard.html"
    ]
    
    for file_path in dashboard_files:
        if Path(file_path).exists():
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} not found")
    
    return True

def run_all_tests():
    """Run all tests"""
    print("🧪 Starting Inventory System Tests\n")
    print("=" * 50)
    
    tests = [
        ("Flask Server", test_flask_server),
        ("Data Import", test_data_import),
        ("Search", test_search_functionality),
        ("Categories", test_categories),
        ("HTML Dashboard", test_html_dashboard)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Your inventory system is ready.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    return passed == len(results)

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1) 