from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required
from app.models.customers import Customers
from app import db

customers_bp = Blueprint('customers', __name__)

@customers_bp.route('/customers')
@login_required
def customers():
    all_customers = Customers.query.all()
    return render_template('customers.html', customers=all_customers)


@customers_bp.route('/customers/add', methods=['GET', 'POST'])
@login_required
def add_customer():
    if request.method == 'POST':
        cust = Customers(
            customer_name=request.form.get("customer_name"),
            phone=request.form.get("phone"),
            address=request.form.get("address"),
            status=request.form.get("status")
        )
        db.session.add(cust)
        db.session.commit()
        return redirect(url_for('customers.customers'))

    return render_template('add_customer.html')


@customers_bp.route('/customers/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_customer(id):
    customer = Customers.query.get_or_404(id)

    if request.method == 'POST':
        customer.customer_name = request.form.get("customer_name")
        customer.phone = request.form.get("phone")
        customer.address = request.form.get("address")
        customer.status = request.form.get("status")
        db.session.commit()
        return redirect(url_for('customers.customers'))

    return render_template('edit_customer.html', customer=customer)


@customers_bp.route('/customers/delete/<int:id>', methods=['POST'])
@login_required
def delete_customer(id):
    customer = Customers.query.get_or_404(id)
    db.session.delete(customer)
    db.session.commit()
    return redirect(url_for('customers.customers'))


@customers_bp.route('/customers/analytics')
@login_required
def customers_analytics():
    total = Customers.query.count()

    active = Customers.query.filter_by(status="Active").count()
    inactive = Customers.query.filter_by(status="Inactive").count()

    city_data = Customers.query.with_entities(
        Customers.address, db.func.count()
    ).group_by(Customers.address).all()

    city_labels = [c[0] for c in city_data]
    city_counts = [c[1] for c in city_data]

    latest_customers = Customers.query.order_by(Customers.id.desc()).limit(10).all()

    return render_template(
        'customers_analytics.html',
        total=total,
        active=active,
        inactive=inactive,
        city_labels=city_labels,
        city_counts=city_counts,
        month_labels=[],
        month_counts=[],
        latest_customers=latest_customers
    )
