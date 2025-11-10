from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required
from app.models.inventory import Inventory
from app import db

inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route('/inventory')
@login_required
def inventory():
    all_inventory = Inventory.query.all()
    return render_template('inventory.html', inventory=all_inventory)


@inventory_bp.route('/inventory/add', methods=['GET', 'POST'])
@login_required
def add_inventory():
    if request.method == 'POST':
        item = Inventory(
            item_name=request.form.get("item_name"),
            quantity=request.form.get("quantity"),
            price=request.form.get("price"),
            unit=request.form.get("unit")
        )
        db.session.add(item)
        db.session.commit()
        return redirect(url_for('inventory.inventory'))

    return render_template('add_inventory.html')


@inventory_bp.route('/inventory/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_inventory(id):
    item = Inventory.query.get_or_404(id)

    if request.method == 'POST':
        item.item_name = request.form.get("item_name")
        item.quantity = request.form.get("quantity")
        item.price = request.form.get("price")
        item.unit = request.form.get("unit")
        db.session.commit()
        return redirect(url_for('inventory.inventory'))

    return render_template('edit_inventory.html', item=item)


@inventory_bp.route('/inventory/delete/<int:id>', methods=['POST'])
@login_required
def delete_inventory(id):
    item = Inventory.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('inventory.inventory'))


@inventory_bp.route('/inventory/analytics')
@login_required
def inventory_analytics():
    total_items = Inventory.query.count()

    total_value = db.session.query(
        db.func.sum(Inventory.quantity * Inventory.price)
    ).scalar() or 0

    low_stock = Inventory.query.filter(Inventory.quantity < 20).all()
    low_labels = [i.item_name for i in low_stock]
    low_values = [i.quantity for i in low_stock]

    top = Inventory.query.order_by(
        (Inventory.quantity * Inventory.price).desc()
    ).limit(10).all()

    top_labels = [i.item_name for i in top]
    top_values = [(i.quantity * i.price) for i in top]

    out_of_stock = Inventory.query.filter(Inventory.quantity == 0).count()
    in_stock = total_items - out_of_stock

    return render_template(
        'inventory_analytics.html',
        total_items=total_items,
        total_value=total_value,
        low_labels=low_labels,
        low_values=low_values,
        top_labels=top_labels,
        top_values=top_values,
        out_of_stock=out_of_stock,
        in_stock=in_stock,
        month_labels=[],
        month_counts=[]
    )
