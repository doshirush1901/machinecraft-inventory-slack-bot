// Global variables
let currentPage = 1;
let currentCategory = 'all';
let currentSearch = '';
let currentSort = 'part_number';
let itemsPerPage = 50;

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    loadCategories();
    loadItems();
    
    // Add event listeners
    document.getElementById('searchInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            searchItems();
        }
    });
});

// Load categories from API
async function loadCategories() {
    try {
        const response = await fetch('/api/categories');
        const categories = await response.json();
        
        const categoriesList = document.getElementById('categoriesList');
        
        // Clear existing categories (except "All Items")
        const allItemsLink = categoriesList.querySelector('[data-category="all"]');
        categoriesList.innerHTML = '';
        categoriesList.appendChild(allItemsLink);
        
        // Add category links
        categories.forEach(category => {
            const link = document.createElement('a');
            link.href = '#';
            link.className = 'list-group-item list-group-item-action';
            link.setAttribute('data-category', category.id);
            link.innerHTML = `
                <i class="fas fa-folder me-2"></i>
                ${category.name}
                <span class="badge bg-secondary float-end">${category.item_count}</span>
            `;
            link.addEventListener('click', function(e) {
                e.preventDefault();
                selectCategory(category.id);
            });
            categoriesList.appendChild(link);
        });
    } catch (error) {
        console.error('Error loading categories:', error);
        showAlert('Error loading categories', 'danger');
    }
}

// Select category
function selectCategory(categoryId) {
    currentCategory = categoryId;
    currentPage = 1;
    
    // Update active state
    document.querySelectorAll('#categoriesList .list-group-item').forEach(item => {
        item.classList.remove('active');
    });
    document.querySelector(`[data-category="${categoryId}"]`).classList.add('active');
    
    loadItems();
}

// Load items from API
async function loadItems() {
    showLoading(true);
    
    try {
        const params = new URLSearchParams({
            page: currentPage,
            per_page: itemsPerPage,
            search: currentSearch
        });
        
        if (currentCategory !== 'all') {
            params.append('category_id', currentCategory);
        }
        
        const response = await fetch(`/api/items?${params}`);
        const data = await response.json();
        
        displayItems(data.items);
        displayPagination(data.total, data.pages, data.current_page);
        
    } catch (error) {
        console.error('Error loading items:', error);
        showAlert('Error loading items', 'danger');
    } finally {
        showLoading(false);
    }
}

// Display items in grid
function displayItems(items) {
    const itemsGrid = document.getElementById('itemsGrid');
    itemsGrid.innerHTML = '';
    
    if (items.length === 0) {
        itemsGrid.innerHTML = `
            <div class="col-12 text-center py-5">
                <i class="fas fa-search fa-3x text-muted mb-3"></i>
                <h4 class="text-muted">No items found</h4>
                <p class="text-muted">Try adjusting your search criteria or category filter.</p>
            </div>
        `;
        return;
    }
    
    items.forEach(item => {
        const itemCard = createItemCard(item);
        itemsGrid.appendChild(itemCard);
    });
}

// Create item card element
function createItemCard(item) {
    const col = document.createElement('div');
    col.className = 'col-lg-4 col-md-6 col-sm-12 mb-4';
    
    const stockStatus = item.actual_quantity <= item.minimum_stock ? 'low' : 'ok';
    const stockClass = item.actual_quantity <= item.minimum_stock ? 'danger' : 'success';
    
    col.innerHTML = `
        <div class="card item-card fade-in" onclick="showItemDetails(${item.id})">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-start mb-2">
                    <h6 class="card-title">${item.part_number}</h6>
                    <span class="badge bg-${stockClass}">${stockStatus.toUpperCase()}</span>
                </div>
                <p class="card-text">${item.description}</p>
                ${item.brand ? `<span class="brand-tag">${item.brand}</span>` : ''}
                <div class="mt-2">
                    ${item.net_price ? `<div class="price">₹${item.net_price.toFixed(2)}</div>` : ''}
                    <div class="quantity ${stockStatus}">
                        <i class="fas fa-boxes me-1"></i>
                        Qty: ${item.actual_quantity}
                        ${item.uom ? ` ${item.uom}` : ''}
                    </div>
                </div>
                ${item.location ? `<small class="text-muted"><i class="fas fa-map-marker-alt me-1"></i>${item.location}</small>` : ''}
            </div>
        </div>
    `;
    
    return col;
}

// Display pagination
function displayPagination(total, pages, currentPage) {
    const pagination = document.getElementById('pagination');
    pagination.innerHTML = '';
    
    if (pages <= 1) return;
    
    // Previous button
    const prevLi = document.createElement('li');
    prevLi.className = `page-item ${currentPage === 1 ? 'disabled' : ''}`;
    prevLi.innerHTML = `<a class="page-link" href="#" onclick="changePage(${currentPage - 1})">Previous</a>`;
    pagination.appendChild(prevLi);
    
    // Page numbers
    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(pages, currentPage + 2);
    
    for (let i = startPage; i <= endPage; i++) {
        const li = document.createElement('li');
        li.className = `page-item ${i === currentPage ? 'active' : ''}`;
        li.innerHTML = `<a class="page-link" href="#" onclick="changePage(${i})">${i}</a>`;
        pagination.appendChild(li);
    }
    
    // Next button
    const nextLi = document.createElement('li');
    nextLi.className = `page-item ${currentPage === pages ? 'disabled' : ''}`;
    nextLi.innerHTML = `<a class="page-link" href="#" onclick="changePage(${currentPage + 1})">Next</a>`;
    pagination.appendChild(nextLi);
}

// Change page
function changePage(page) {
    currentPage = page;
    loadItems();
}

// Search items
function searchItems() {
    currentSearch = document.getElementById('searchInput').value.trim();
    currentPage = 1;
    loadItems();
}

// Show item details modal
async function showItemDetails(itemId) {
    try {
        const response = await fetch(`/api/items/${itemId}`);
        const item = await response.json();
        
        const modalBody = document.getElementById('itemModalBody');
        modalBody.innerHTML = `
            <form id="itemForm">
                <div class="row">
                    <div class="col-md-6">
                        <div class="mb-3">
                            <label class="form-label">Part Number</label>
                            <input type="text" class="form-control" name="part_number" value="${item.part_number || ''}" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Description</label>
                            <textarea class="form-control" name="description" rows="3" required>${item.description || ''}</textarea>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Brand</label>
                            <input type="text" class="form-control" name="brand" value="${item.brand || ''}">
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="mb-3">
                            <label class="form-label">List Price</label>
                            <input type="number" class="form-control" name="list_price" value="${item.list_price || ''}" step="0.01">
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Net Price</label>
                            <input type="number" class="form-control" name="net_price" value="${item.net_price || ''}" step="0.01">
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Minimum Stock</label>
                            <input type="number" class="form-control" name="minimum_stock" value="${item.minimum_stock || 0}">
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Actual Quantity</label>
                            <input type="number" class="form-control" name="actual_quantity" value="${item.actual_quantity || 0}">
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Location</label>
                            <input type="text" class="form-control" name="location" value="${item.location || ''}">
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Rack</label>
                            <input type="text" class="form-control" name="rack" value="${item.rack || ''}">
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Unit of Measure</label>
                            <input type="text" class="form-control" name="uom" value="${item.uom || ''}">
                        </div>
                    </div>
                </div>
            </form>
        `;
        
        // Store item ID for saving
        modalBody.setAttribute('data-item-id', itemId);
        
        const modal = new bootstrap.Modal(document.getElementById('itemModal'));
        modal.show();
        
    } catch (error) {
        console.error('Error loading item details:', error);
        showAlert('Error loading item details', 'danger');
    }
}

// Save item changes
async function saveItemChanges() {
    const modalBody = document.getElementById('itemModalBody');
    const itemId = modalBody.getAttribute('data-item-id');
    const form = document.getElementById('itemForm');
    
    const formData = new FormData(form);
    const data = {};
    
    for (let [key, value] of formData.entries()) {
        if (value !== '') {
            if (['list_price', 'net_price', 'minimum_stock', 'actual_quantity'].includes(key)) {
                data[key] = parseFloat(value) || 0;
            } else {
                data[key] = value;
            }
        }
    }
    
    try {
        const response = await fetch(`/api/items/${itemId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            showAlert('Item updated successfully', 'success');
            bootstrap.Modal.getInstance(document.getElementById('itemModal')).hide();
            loadItems(); // Refresh the items list
        } else {
            throw new Error('Failed to update item');
        }
    } catch (error) {
        console.error('Error updating item:', error);
        showAlert('Error updating item', 'danger');
    }
}

// Import data from Excel files
async function importData() {
    if (!confirm('This will import data from all Excel files in the inventory folder. Continue?')) {
        return;
    }
    
    showLoading(true);
    
    try {
        const response = await fetch('/api/import', {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showAlert(result.message, 'success');
            loadCategories();
            loadItems();
        } else {
            showAlert(`Import failed: ${result.error}`, 'danger');
        }
    } catch (error) {
        console.error('Error importing data:', error);
        showAlert('Error importing data', 'danger');
    } finally {
        showLoading(false);
    }
}

// Show statistics
async function showStats() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();
        
        const modalBody = document.getElementById('statsModalBody');
        modalBody.innerHTML = `
            <div class="row">
                <div class="col-md-4">
                    <div class="stats-card">
                        <h3>${stats.total_items}</h3>
                        <p>Total Items</p>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="stats-card">
                        <h3>${stats.low_stock_items}</h3>
                        <p>Low Stock Items</p>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="stats-card">
                        <h3>${stats.categories_count}</h3>
                        <p>Categories</p>
                    </div>
                </div>
            </div>
            
            <div class="mt-4">
                <h5>Top Categories</h5>
                <div class="list-group">
                    ${stats.top_categories.map(cat => `
                        <div class="list-group-item d-flex justify-content-between align-items-center">
                            ${cat.name}
                            <span class="badge bg-primary rounded-pill">${cat.count}</span>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
        
        const modal = new bootstrap.Modal(document.getElementById('statsModal'));
        modal.show();
        
    } catch (error) {
        console.error('Error loading statistics:', error);
        showAlert('Error loading statistics', 'danger');
    }
}

// Show loading spinner
function showLoading(show) {
    const spinner = document.getElementById('loadingSpinner');
    spinner.style.display = show ? 'flex' : 'none';
}

// Show alert message
function showAlert(message, type) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
} 