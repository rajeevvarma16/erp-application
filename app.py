# from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
# from flask_sqlalchemy import SQLAlchemy
# from flask_login import (
#     LoginManager, UserMixin, login_user, logout_user,
#     login_required, current_user
# )
# from flask_limiter import Limiter
# from flask_limiter.util import get_remote_address
# from datetime import datetime, date
# import pymysql, os
# from werkzeug.security import generate_password_hash, check_password_hash


# pymysql.install_as_MySQLdb()

# # --------------------------------------------------
# # App + DB Setup
# # --------------------------------------------------
# db = SQLAlchemy()
# app = Flask(__name__)

# app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:password@localhost:3306/testing"
# app.config['SECRET_KEY'] = os.urandom(24)

# db.init_app(app)

# # --------------------------------------------------
# # Login Manager
# # --------------------------------------------------
# login_manager = LoginManager()
# login_manager.login_view = 'login'
# login_manager.init_app(app)

# @login_manager.user_loader
# def load_user(user_id):
#     return Users.query.get(int(user_id))

# # --------------------------------------------------
# # Rate Limiter
# # --------------------------------------------------
# limiter = Limiter(
#     key_func=get_remote_address,
#     default_limits=["200 per day", "50 per hour"],
#     app=app
# )

# # --------------------------------------------------
# # Models
# # --------------------------------------------------
# class Users(UserMixin, db.Model):
#     __tablename__ = 'users'
#     id = db.Column(db.Integer, primary_key=True)
#     username = db.Column(db.String(100), nullable=False)
#     password = db.Column(db.String(255), nullable=False)
#     email = db.Column(db.String(100), unique=True, nullable=False)


# class Employees(db.Model):
#     __tablename__ = 'employees'
#     id = db.Column(db.Integer, primary_key=True)
#     employee_name = db.Column(db.String(100), nullable=False)
#     department = db.Column(db.String(100), nullable=False)
#     joining_date = db.Column(db.Date, nullable=False, default=lambda: date.today())
#     salary = db.Column(db.Integer, nullable=False)
#     status = db.Column(db.String(20), nullable=False)


# class Customers(db.Model):
#     __tablename__ = 'customers'
#     id = db.Column(db.Integer, primary_key=True)
#     customer_name = db.Column(db.String(100))
#     phone = db.Column(db.String(20))
#     address = db.Column(db.String(800))
#     status = db.Column(db.String(50))


# class Vendors(db.Model):
#     __tablename__ = 'vendors'
#     id = db.Column(db.Integer, primary_key=True)
#     vendor_name = db.Column(db.String(100))
#     contact_person = db.Column(db.String(100))
#     phone = db.Column(db.String(20))
#     category = db.Column(db.String(100))


# class Inventory(db.Model):
#     __tablename__ = 'inventory'
#     id = db.Column(db.Integer, primary_key=True)
#     item_name = db.Column(db.String(100))
#     quantity = db.Column(db.Integer)
#     price = db.Column(db.Integer)
#     unit = db.Column(db.String(20))


# # --------------------------------------------------
# # Auth Routes
# # --------------------------------------------------
# @app.route('/')
# def home():
#     return redirect(url_for('login'))

# @app.route('/login', methods=['GET', 'POST'])
# @limiter.limit("10 per minute")
# def login():
#     if request.method == 'POST':
#         username = request.form.get('username')
#         password = request.form.get('password')

#         user = Users.query.filter_by(username=username).first()

#         if user and check_password_hash(user.password, password):
#             login_user(user)
#             return redirect(url_for('protected'))

#         flash("Invalid username or password")
#         return redirect(url_for('login'))

#     return render_template('login.html')


# @app.route('/register', methods=['GET', 'POST'])
# @limiter.limit("10 per minute")
# def register():
#     if request.method == 'POST':
#         username = request.form.get('username')
#         email = request.form.get('email')
#         password = generate_password_hash(request.form.get('password'))

#         new_user = Users(username=username, email=email, password=password)
#         db.session.add(new_user)
#         db.session.commit()

#         return redirect(url_for('login'))

#     return render_template('register.html')


# @app.route('/protected')
# @login_required
# def protected():
#     return render_template('landing.html')


# @app.route('/logout')
# @login_required
# def logout():
#     logout_user()
#     return redirect(url_for('login'))

# # --------------------------------------------------
# # dashboard
# # --------------------------------------------------

# @app.route('/dashboard')
# @login_required
# def dashboard():
#     emp_count = Employees.query.count()
#     vendor_count = Vendors.query.count()
#     customer_count = Customers.query.count()
#     inventory_count = Inventory.query.count()

#     total_stock_value = db.session.query(
#         db.func.sum(Inventory.quantity * Inventory.price)
#     ).scalar() or 0

#     active_customers = Customers.query.filter_by(status="Active").count()
#     inactive_customers = Customers.query.filter_by(status="Inactive").count()

#     return render_template(
#         'dashboard.html',
#         emp_count=emp_count,
#         vendor_count=vendor_count,
#         customer_count=customer_count,
#         inventory_count=inventory_count,
#         total_stock_value=total_stock_value,
#         active_customers=active_customers,
#         inactive_customers=inactive_customers
#     )



# # --------------------------------------------------
# # EMPLOYEES
# # --------------------------------------------------
# @app.route('/employees')
# @login_required
# def employees():
#     all_employees = Employees.query.all()
#     return render_template('employees.html', employees=all_employees)


# @app.route('/employees/add', methods=['GET', 'POST'])
# @login_required
# def add_employee():
#     if request.method == 'POST':
#         emp = Employees(
#             employee_name=request.form.get("employee_name"),
#             status=request.form.get("status"),
#             department=request.form.get("department"),
#             salary=request.form.get("salary"),
#             joining_date=datetime.strptime(request.form.get("joining_date"), "%Y-%m-%d").date()
#         )
#         db.session.add(emp)
#         db.session.commit()
#         return redirect(url_for('employees'))

#     return render_template('add_employee.html')


# @app.route('/employees/edit/<int:id>', methods=['GET', 'POST'])
# @login_required
# def edit_employee(id):
#     employee = Employees.query.get_or_404(id)

#     if request.method == 'POST':
#         employee.employee_name = request.form.get("employee_name")
#         employee.status = request.form.get("status")
#         employee.department = request.form.get("department")
#         employee.salary = request.form.get("salary")
#         employee.joining_date = datetime.strptime(request.form.get("joining_date"), "%Y-%m-%d").date()
#         db.session.commit()
#         return redirect(url_for('employees'))

#     return render_template('edit_employee.html', employee=employee)


# @app.route('/employees/delete/<int:id>', methods=['POST'])
# @login_required
# def delete_employee(id):
#     emp = Employees.query.get_or_404(id)
#     db.session.delete(emp)
#     db.session.commit()
#     return redirect(url_for('employees'))

# @app.route('/employees/analytics')
# @login_required
# def employees_analytics():
#     total = Employees.query.count()

#     # Department breakdown
#     dept_data = Employees.query.with_entities(
#         Employees.department, db.func.count()
#     ).group_by(Employees.department).all()
#     dept_labels = [d[0] for d in dept_data]
#     dept_counts = [d[1] for d in dept_data]

#     # Status breakdown
#     active = Employees.query.filter_by(status="Active").count()
#     inactive = Employees.query.filter_by(status="Inactive").count()

#     # Monthly hiring
#     month_data = db.session.query(
#         db.func.month(Employees.joining_date),
#         db.func.count()
#     ).group_by(db.func.month(Employees.joining_date)).all()

#     month_labels = [f"Month {m[0]}" for m in month_data]
#     month_counts = [m[1] for m in month_data]

#     # Latest employees
#     latest = Employees.query.order_by(Employees.id.desc()).limit(10).all()

#     return render_template(
#         'employees_analytics.html',
#         total=total,
#         active=active,
#         inactive=inactive,
#         dept_labels=dept_labels,
#         dept_counts=dept_counts,
#         month_labels=month_labels,
#         month_counts=month_counts,
#         latest=latest
#     )




# # --------------------------------------------------
# # VENDORS
# # --------------------------------------------------
# @app.route('/vendors')
# @login_required
# def vendors():
#     all_vendors = Vendors.query.all()
#     return render_template('vendors.html', vendors=all_vendors)


# @app.route('/vendors/add', methods=['GET', 'POST'])
# @login_required
# def add_vendor():
#     if request.method == 'POST':
#         vendor = Vendors(
#             vendor_name=request.form.get("name"),
#             contact_person=request.form.get("contact_person"),
#             phone=request.form.get("phone"),
#             category=request.form.get("category")
#         )
#         db.session.add(vendor)
#         db.session.commit()
#         return redirect(url_for('vendors'))

#     return render_template('add_vendor.html')


# @app.route('/vendors/edit/<int:id>', methods=['GET', 'POST'])
# @login_required
# def edit_vendor(id):
#     vendor = Vendors.query.get_or_404(id)

#     if request.method == 'POST':
#         vendor.vendor_name = request.form.get("name")
#         vendor.contact_person = request.form.get("contact_person")
#         vendor.phone = request.form.get("phone")
#         vendor.category = request.form.get("category")
#         db.session.commit()
#         return redirect(url_for('vendors'))

#     return render_template('edit_vendor.html', vendor=vendor)


# @app.route('/vendors/delete/<int:id>', methods=['POST'])
# @login_required
# def delete_vendor(id):
#     vendor = Vendors.query.get_or_404(id)
#     db.session.delete(vendor)
#     db.session.commit()
#     return redirect(url_for('vendors'))

# @app.route('/vendors/analytics')
# @login_required
# def vendors_analytics():
#     total_vendors = Vendors.query.count()

#     # Category breakdown
#     cat_data = Vendors.query.with_entities(
#         Vendors.category, db.func.count()
#     ).group_by(Vendors.category).all()

#     cat_labels = [row[0] for row in cat_data]
#     cat_counts = [row[1] for row in cat_data]

#     # Vendors with missing phone
#     missing_phone = Vendors.query.filter(
#         (Vendors.phone == None) | (Vendors.phone == "")
#     ).count()
#     with_phone = total_vendors - missing_phone

#     # Latest vendors
#     latest = Vendors.query.order_by(Vendors.id.desc()).limit(10).all()

#     # Monthly vendors - using ID created order (no date column)
#     # If you want REAL monthly vendors, add created_at column.
#     month_labels = []
#     month_counts = []

#     return render_template(
#         'vendors_analytics.html',
#         total_vendors=total_vendors,
#         cat_labels=cat_labels,
#         cat_counts=cat_counts,
#         missing_phone=missing_phone,
#         with_phone=with_phone,
#         latest=latest,
#         month_labels=month_labels,
#         month_counts=month_counts
#     )



# # --------------------------------------------------
# # INVENTORY
# # --------------------------------------------------
# @app.route('/inventory')
# @login_required
# def inventory():
#     all_inventory = Inventory.query.all()
#     return render_template('inventory.html', inventory=all_inventory)


# @app.route('/inventory/add', methods=['GET', 'POST'])
# @login_required
# def add_inventory():
#     if request.method == 'POST':
#         item = Inventory(
#             item_name=request.form.get("item_name"),
#             quantity=request.form.get("quantity"),
#             price=request.form.get("price"),
#             unit=request.form.get("unit")
#         )
#         db.session.add(item)
#         db.session.commit()
#         return redirect(url_for('inventory'))

#     return render_template('add_inventory.html')


# @app.route('/inventory/edit/<int:id>', methods=['GET', 'POST'])
# @login_required
# def edit_inventory(id):
#     item = Inventory.query.get_or_404(id)

#     if request.method == 'POST':
#         item.item_name = request.form.get("item_name")
#         item.quantity = request.form.get("quantity")
#         item.price = request.form.get("price")
#         item.unit = request.form.get("unit")
#         db.session.commit()
#         return redirect(url_for('inventory'))

#     return render_template('edit_inventory.html', item=item)


# @app.route('/inventory/delete/<int:id>', methods=['POST'])
# @login_required
# def delete_inventory(id):
#     item = Inventory.query.get_or_404(id)
#     db.session.delete(item)
#     db.session.commit()
#     return redirect(url_for('inventory'))


# @app.route('/inventory/analytics')
# @login_required
# def inventory_analytics():
#     total_items = Inventory.query.count()

#     total_value = db.session.query(
#         db.func.sum(Inventory.quantity * Inventory.price)
#     ).scalar() or 0

#     # Low stock (< 20)
#     low_stock = Inventory.query.filter(Inventory.quantity < 20).all()
#     low_labels = [i.item_name for i in low_stock]
#     low_values = [i.quantity for i in low_stock]

#     # Highest value items
#     top = Inventory.query.order_by(
#         (Inventory.quantity * Inventory.price).desc()
#     ).limit(10).all()
#     top_labels = [i.item_name for i in top]
#     top_values = [(i.quantity * i.price) for i in top]

#     # Out of stock
#     out_of_stock = Inventory.query.filter(Inventory.quantity == 0).count()
#     in_stock = total_items - out_of_stock

#     # Monthly stock changes – requires a stock_history table
#     month_labels = []
#     month_counts = []

#     return render_template(
#         'inventory_analytics.html',
#         total_items=total_items,
#         total_value=total_value,
#         low_labels=low_labels,
#         low_values=low_values,
#         top_labels=top_labels,
#         top_values=top_values,
#         out_of_stock=out_of_stock,
#         in_stock=in_stock,
#         month_labels=month_labels,
#         month_counts=month_counts
#     )



# # --------------------------------------------------
# # CUSTOMERS
# # --------------------------------------------------
# @app.route('/customers')
# @login_required
# def customers():
#     all_customers = Customers.query.all()
#     return render_template('customers.html', customers=all_customers)


# @app.route('/customers/add', methods=['GET', 'POST'])
# @login_required
# def add_customer():
#     if request.method == 'POST':
#         cust = Customers(
#             customer_name=request.form.get("customer_name"),
#             phone=request.form.get("phone"),
#             address=request.form.get("address"),
#             status=request.form.get("status")
#         )
#         db.session.add(cust)
#         db.session.commit()
#         return redirect(url_for('customers'))

#     return render_template('add_customer.html')


# @app.route('/customers/edit/<int:id>', methods=['GET', 'POST'])
# @login_required
# def edit_customer(id):
#     customer = Customers.query.get_or_404(id)

#     if request.method == 'POST':
#         customer.customer_name = request.form.get("customer_name")
#         customer.phone = request.form.get("phone")
#         customer.address = request.form.get("address")
#         customer.status = request.form.get("status")
#         db.session.commit()
#         return redirect(url_for('customers'))

#     return render_template('edit_customer.html', customer=customer)


# @app.route('/customers/delete/<int:id>', methods=['POST'])
# @login_required
# def delete_customer(id):
#     customer = Customers.query.get_or_404(id)
#     db.session.delete(customer)
#     db.session.commit()
#     return redirect(url_for('customers'))

# @app.route('/customers/analytics')
# @login_required
# def customers_analytics():
#     # Total
#     total = Customers.query.count()

#     # Active / Inactive
#     active = Customers.query.filter_by(status="Active").count()
#     inactive = Customers.query.filter_by(status="Inactive").count()

#     # City breakdown
#     city_data = Customers.query.with_entities(
#         Customers.address, db.func.count()
#     ).group_by(Customers.address).all()
#     city_labels = [row[0] for row in city_data]
#     city_counts = [row[1] for row in city_data]

#     # NEW: Monthly new customers (last 12 months)
#     month_data = db.session.query(
#         db.func.month(Employees.joining_date),
#         db.func.count()
#     ).group_by(db.func.month(Employees.joining_date)).all()

#     # Convert to chart lists
#     month_labels = [f"Month {m[0]}" for m in month_data]
#     month_counts = [m[1] for m in month_data]

#     # Latest 10 customers
#     latest_customers = Customers.query.order_by(Customers.id.desc()).limit(10).all()

#     return render_template(
#         'customers_analytics.html',
#         total=total,
#         active=active,
#         inactive=inactive,
#         city_labels=city_labels,
#         city_counts=city_counts,
#         month_labels=month_labels,
#         month_counts=month_counts,
#         latest_customers=latest_customers
#     )



# # --------------------------------------------------
# # Error Handling
# # --------------------------------------------------
# @app.errorhandler(429)
# def ratelimit_handler(error):
#     flash("Too many attempts. Please wait a minute and try again.")
#     return render_template('login.html'), 429


# @app.route("/api/chatbot", methods=["POST"])
# def chatbot():
#     from openai import OpenAI
#     import os
#     client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

#     data = request.get_json()
#     user_query = data.get("query", "")

#     response = client.chat.completions.create(
#         model="gpt-4.1-mini",
#         messages=[
#             {"role": "system", "content": "You are an ERP assistant."},
#             {"role": "user", "content": user_query}
#         ]
#     )

#     reply = response.choices[0].message.content
#     return jsonify({"reply": reply})


# # --------------------------------------------------
# # Start App
# # --------------------------------------------------
# if __name__ == "__main__":
#     with app.app_context():
#         db.create_all()
#     app.run(debug=True, port=8000)
