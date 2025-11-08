from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask import flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from datetime import datetime, date
import os
import pymysql
pymysql.install_as_MySQLdb()


db = SQLAlchemy()
app = Flask(__name__)
class Users(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)


class Employees(db.Model):
    __tablename__ = 'employees'

    id = db.Column(db.Integer, primary_key=True)
    employee_name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    joining_date = db.Column(db.Date, nullable=False, default=lambda: date.today())
    salary = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False)

class Customers(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(800))
    status = db.Column(db.String(50))

class Vendors(db.Model):
    __tablename__ = 'vendors'
    id = db.Column(db.Integer, primary_key=True)
    vendor_name = db.Column(db.String(100))
    contact_person = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    category = db.Column(db.String(100))

class Inventory(db.Model):
    __tablename__ = 'inventory'
    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(100))
    quantity = db.Column(db.Integer)
    price = db.Column(db.Integer)
    unit = db.Column(db.String(20))


    
# app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"

app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:password@localhost:3306/testing"
app.config['SECRET_KEY'] = os.urandom(24)

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # redirect unauthorized users here

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    
)

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    if request.method == 'POST':
        username = request.form.get('username')  # from login.html input
        password = request.form.get('password')

        # 1️⃣ check if user exists
        user = Users.query.filter_by(username=username).first()
        #if user and user.password == password:
        if user and check_password_hash(user.password, password):
            login_user(user)                     # 3️⃣ actually log them in
            
            #return redirect('/protected')
            return redirect(url_for('protected'))

        flash("Invalid username or password")
        return redirect(url_for('login'))
        #return "Invalid credentials!"
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def register():
    if request.method == 'POST':
        username = request.form.get('username')   # matches input name
        email = request.form.get('email')
        password = request.form.get('password')

        hashed_pw = generate_password_hash(password)

        new_user = Users(
            username=username,
            email=email,
            password=hashed_pw
        )
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))  # after successful register

    # if it's a GET request, show the register page
    return render_template('register.html')


@app.route('/protected')
@login_required
def protected():
    return render_template('landing.html')
    #return f'''✅ Logged in as: {current_user.username} <br> <a href="{url_for('logout')}">Logout</a>'''


@app.route('/employees', methods=['GET', 'POST'])
@login_required
def employees():

    all_employees = Employees.query.all()
    return render_template('employees.html', employees=all_employees)

@app.route('/employees/add', methods=['GET', 'POST'])
@login_required
def add_employee():
    if request.method == 'POST':
        name = request.form.get("employee_name")
        status = request.form.get("status")
        dept = request.form.get("department")
        salary = request.form.get("salary")
        joining_date = datetime.strptime(request.form.get("joining_date"), "%Y-%m-%d").date()

        new_emp = Employees(
            employee_name=name,
            status=status,
            department=dept,
            salary=salary,
            joining_date=joining_date
        )

        db.session.add(new_emp)
        db.session.commit()

        return redirect('/employees')

    return render_template('add_employee.html')


@app.route('/employees/delete/<int:id>', methods=['POST'])
@login_required
def delete_employee(id):
    emp = Employees.query.get_or_404(id)
    db.session.delete(emp)
    db.session.commit()
    return redirect('/employees')

@app.route('/employees/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_employee(id):
    employee = Employees.query.get_or_404(id)

    if request.method == 'POST':
        employee.employee_name = request.form.get("employee_name")
        employee.status = request.form.get("status")
        employee.department = request.form.get("department")
        employee.salary = request.form.get("salary")
        employee.joining_date = datetime.strptime(request.form.get("joining_date"), "%Y-%m-%d").date()

        db.session.commit()
        return redirect('/employees')

    return render_template('edit_employee.html', employee=employee)

@app.route('/vendors', methods=['GET', 'POST'])
@login_required
def vendors():

    all_vendors = Vendors.query.all()
    return render_template('vendors.html', vendors=all_vendors)

@app.route('/vendors/add', methods=['GET', 'POST'])
@login_required
def add_vendor():
    if request.method == 'POST':
        name = request.form.get("name")
        contact = request.form.get("contact_person")
        phone = request.form.get("phone")
        category = request.form.get("category")

        new_vendor = Vendors(
            vendor_name=name,
            contact_person=contact,
            phone=phone,
            category=category
        )

        db.session.add(new_vendor)
        db.session.commit()

        return redirect('/vendors')

    return render_template('add_vendor.html')


@app.route('/vendors/delete/<int:id>', methods=['POST'])
@login_required
def delete_vendor(id):
    vendor = Vendors.query.get_or_404(id)
    db.session.delete(vendor)
    db.session.commit()
    return redirect('/vendors')

@app.route('/vendors/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_vendor(id):
    vendor = Vendors.query.get_or_404(id)

    if request.method == 'POST':
        vendor.vendor_name = request.form.get("name")
        vendor.contact_person = request.form.get("contact_person")
        vendor.phone = request.form.get("phone")
        vendor.category = request.form.get("category")

        db.session.commit()

        return redirect('/vendors')

    return render_template('edit_vendor.html', vendor=vendor)


@app.route('/inventory', methods=['GET', 'POST'])
@login_required
def inventory():

    all_inventory = Inventory.query.all()
    return render_template('inventory.html', inventory=all_inventory)

@app.route('/inventory/add', methods=['GET', 'POST'])
@login_required
def add_inventory():
    if request.method == 'POST':
        item_name = request.form.get("item_name")
        qty = request.form.get("quantity")
        price = request.form.get("price")
        unit = request.form.get("unit")

        new_item = Inventory(
            item_name=item_name,
            quantity=qty,
            price=price,
            unit=unit
        )

        db.session.add(new_item)
        db.session.commit()

        return redirect('/inventory')

    return render_template('add_inventory.html')





@app.route('/inventory/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_inventory(id):
    item = Inventory.query.get_or_404(id)

    if request.method == 'POST':
        item.item_name = request.form.get("item_name")
        item.quantity = request.form.get("quantity")
        item.price = request.form.get("price")
        item.unit = request.form.get("unit")

        db.session.commit()
        return redirect('/inventory')

    return render_template('edit_inventory.html', item=item)

@app.route('/inventory/delete/<int:id>', methods=['POST'])
@login_required
def delete_inventory(id):
    item = Inventory.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    return redirect('/inventory')

@app.route('/customers', methods=['GET', 'POST'])
@login_required
def customers():
    
    all_customers = Customers.query.all()
    return render_template('customers.html', customers=all_customers)

@app.route('/customers/add', methods=['GET', 'POST'])
@login_required
def add_customer():
    if request.method == 'POST':
        name = request.form.get("customer_name")
        phone = request.form.get("phone")
        address = request.form.get("address")
        status = request.form.get("status")

        new_customer = Customers(
            customer_name=name,
            phone=phone,
            address=address,
            status=status
        )
        db.session.add(new_customer)
        db.session.commit()

        return redirect('/customers')

    return render_template('add_customer.html')


@app.route('/customers/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_customer(id):
    customer = Customers.query.get_or_404(id)

    if request.method == 'POST':
        customer.customer_name = request.form.get("customer_name")
        customer.phone = request.form.get("phone")
        customer.address = request.form.get("address")
        customer.status = request.form.get("status")

        db.session.commit()
        return redirect('/customers')

    return render_template('edit_customer.html', customer=customer)

@app.route('/customers/delete/<int:id>', methods=['POST'])
@login_required
def delete_customer(id):
    customer = Customers.query.get_or_404(id)
    db.session.delete(customer)
    db.session.commit()
    return redirect('/customers')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    #return 'Logged out'
    return redirect(url_for('login'))

@app.errorhandler(429)
def ratelimit_handler(error):
    flash("Too many attempts. Please wait a minute and try again.")
    return render_template('login.html'), 429


if __name__ == "__main__":
    # ✅ ensure DB and tables exist every time you start app
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=8000)
