from flask import Blueprint, render_template
from flask_login import login_required
from app.models.employees import Employees
from app.models.customers import Customers
from app.models.vendors import Vendors
from app.models.inventory import Inventory
from app import db

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    emp_count = Employees.query.count()
    vendor_count = Vendors.query.count()
    customer_count = Customers.query.count()
    inventory_count = Inventory.query.count()

    total_stock_value = db.session.query(
        db.func.sum(Inventory.quantity * Inventory.price)
    ).scalar() or 0

    active_customers = Customers.query.filter_by(status="Active").count()
    inactive_customers = Customers.query.filter_by(status="Inactive").count()

    return render_template(
        'dashboard.html',
        emp_count=emp_count,
        vendor_count=vendor_count,
        customer_count=customer_count,
        inventory_count=inventory_count,
        total_stock_value=total_stock_value,
        active_customers=active_customers,
        inactive_customers=inactive_customers
    )
