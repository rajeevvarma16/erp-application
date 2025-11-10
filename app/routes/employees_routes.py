from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required
from datetime import datetime
from app.models.employees import Employees
from app import db

employees_bp = Blueprint('employees', __name__)

@employees_bp.route('/employees')
@login_required
def employees():
    all_employees = Employees.query.all()
    return render_template('employees.html', employees=all_employees)


@employees_bp.route('/employees/add', methods=['GET', 'POST'])
@login_required
def add_employee():
    if request.method == 'POST':
        emp = Employees(
            employee_name=request.form.get("employee_name"),
            status=request.form.get("status"),
            department=request.form.get("department"),
            salary=request.form.get("salary"),
            joining_date=datetime.strptime(
                request.form.get("joining_date"),
                "%Y-%m-%d"
            ).date()
        )
        db.session.add(emp)
        db.session.commit()
        return redirect(url_for('employees.employees'))

    return render_template('add_employee.html')


@employees_bp.route('/employees/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_employee(id):
    employee = Employees.query.get_or_404(id)

    if request.method == 'POST':
        employee.employee_name = request.form.get("employee_name")
        employee.status = request.form.get("status")
        employee.department = request.form.get("department")
        employee.salary = request.form.get("salary")
        employee.joining_date = datetime.strptime(
            request.form.get("joining_date"),
            "%Y-%m-%d"
        ).date()

        db.session.commit()
        return redirect(url_for('employees.employees'))

    return render_template('edit_employee.html', employee=employee)


@employees_bp.route('/employees/delete/<int:id>', methods=['POST'])
@login_required
def delete_employee(id):
    emp = Employees.query.get_or_404(id)
    db.session.delete(emp)
    db.session.commit()
    return redirect(url_for('employees.employees'))


@employees_bp.route('/employees/analytics')
@login_required
def employees_analytics():
    total = Employees.query.count()

    dept_data = Employees.query.with_entities(
        Employees.department, db.func.count()
    ).group_by(Employees.department).all()

    dept_labels = [d[0] for d in dept_data]
    dept_counts = [d[1] for d in dept_data]

    active = Employees.query.filter_by(status="Active").count()
    inactive = Employees.query.filter_by(status="Inactive").count()

    month_data = db.session.query(
        db.func.month(Employees.joining_date),
        db.func.count()
    ).group_by(db.func.month(Employees.joining_date)).all()

    month_labels = [f"Month {m[0]}" for m in month_data]
    month_counts = [m[1] for m in month_data]

    latest = Employees.query.order_by(Employees.id.desc()).limit(10).all()

    return render_template(
        'employees_analytics.html',
        total=total,
        active=active,
        inactive=inactive,
        dept_labels=dept_labels,
        dept_counts=dept_counts,
        month_labels=month_labels,
        month_counts=month_counts,
        latest=latest
    )
