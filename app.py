from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask import flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
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

@app.route('/employees')
@login_required
def employees():
    return render_template('employees.html')

@app.route('/vendors')
@login_required
def vendors():
    return render_template('vendors.html')

@app.route('/inventory')
@login_required
def inventory():
    return render_template('inventory.html')

    


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
