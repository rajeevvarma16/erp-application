from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required
from app.models.vendors import Vendors
from app import db

vendors_bp = Blueprint('vendors', __name__)

@vendors_bp.route('/vendors')
@login_required
def vendors():
    all_vendors = Vendors.query.all()
    return render_template('vendors.html', vendors=all_vendors)


@vendors_bp.route('/vendors/add', methods=['GET', 'POST'])
@login_required
def add_vendor():
    if request.method == 'POST':
        vendor = Vendors(
            vendor_name=request.form.get("name"),
            contact_person=request.form.get("contact_person"),
            phone=request.form.get("phone"),
            category=request.form.get("category")
        )
        db.session.add(vendor)
        db.session.commit()
        return redirect(url_for('vendors.vendors'))

    return render_template('add_vendor.html')


@vendors_bp.route('/vendors/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_vendor(id):
    vendor = Vendors.query.get_or_404(id)

    if request.method == 'POST':
        vendor.vendor_name = request.form.get("name")
        vendor.contact_person = request.form.get("contact_person")
        vendor.phone = request.form.get("phone")
        vendor.category = request.form.get("category")
        db.session.commit()
        return redirect(url_for('vendors.vendors'))

    return render_template('edit_vendor.html', vendor=vendor)


@vendors_bp.route('/vendors/delete/<int:id>', methods=['POST'])
@login_required
def delete_vendor(id):
    vendor = Vendors.query.get_or_404(id)
    db.session.delete(vendor)
    db.session.commit()
    return redirect(url_for('vendors.vendors'))


@vendors_bp.route('/vendors/analytics')
@login_required
def vendors_analytics():
    total_vendors = Vendors.query.count()

    cat_data = Vendors.query.with_entities(
        Vendors.category, db.func.count()
    ).group_by(Vendors.category).all()

    cat_labels = [c[0] for c in cat_data]
    cat_counts = [c[1] for c in cat_data]

    missing_phone = Vendors.query.filter(
        (Vendors.phone == None) | (Vendors.phone == "")
    ).count()

    with_phone = total_vendors - missing_phone

    latest = Vendors.query.order_by(Vendors.id.desc()).limit(10).all()

    return render_template(
        'vendors_analytics.html',
        total_vendors=total_vendors,
        cat_labels=cat_labels,
        cat_counts=cat_counts,
        missing_phone=missing_phone,
        with_phone=with_phone,
        latest=latest,
        month_labels=[],
        month_counts=[]
    )
