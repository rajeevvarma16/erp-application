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
    new_employee = Employees(
            employee_name="Rajeev",
            status="Active",
            department="IT",
            salary=70000,
            joining_date=datetime.strptime("2023-01-15", "%Y-%m-%d").date()
        )
    db.session.add(new_employee)
    db.session.commit()

    all_employees = Employees.query.all()

    return render_template('employees.html', employees=all_employees)

@app.route('/vendors')
@login_required
def vendors():

    dummy = Vendors(
        vendor_name="ABC Suppliers",
        contact_person="Ramesh",
        phone="9876001234",
        category="Hardware"
    )
    db.session.add(dummy)
    db.session.commit()

    all_vendors = Vendors.query.all()
    return render_template('vendors.html', vendors=all_vendors)
    #return render_template('vendors.html')

@app.route('/inventory')
@login_required
def inventory():
    dummy = Inventory(
        item_name="Cement Bag",
        quantity=50,
        price=350,
        unit="Bags"
    )
    db.session.add(dummy)
    db.session.commit()

    all_items = Inventory.query.all()
    return render_template('inventory.html', inventory=all_items)

    #return render_template('inventory.html')

@app.route('/customers')
@login_required
def customers():

    new_customer = Customers(
        customer_name="John Enterprises",
        phone="9876543210",
        address="Hyderabad, Telangana",
        status="Active"
        )
    db.session.add(new_customer)
    db.session.commit()

    all_customers = Customers.query.all()

    return render_template('customers.html', customers=all_customers)

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
