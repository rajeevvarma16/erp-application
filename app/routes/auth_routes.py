from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.users import Users
from app import db, limiter

# Flask-WTF
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, Email, ValidationError

auth_bp = Blueprint('auth', __name__)

# -------------------- FORMS --------------------
class LoginForm(FlaskForm):
    # match EXACT HTML input name="username"
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=50)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=6, max=20)])
    submit = SubmitField('Login')


class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[InputRequired(), Length(min=4, max=50), Email()])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=6, max=20)])
    submit = SubmitField('Register')

    def validate_email(self, field):
        user = Users.query.filter_by(email=field.data.lower()).first()
        if user:
            raise ValidationError("Email already exists. Please choose another one.")

    def validate_username(self, field):
        user = Users.query.filter_by(username=field.data).first()
        if user:
            raise ValidationError("Username already exists. Please choose another one.")
# ------------------------------------------------


@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = Users.query.filter_by(username=form.username.data).first()

        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('auth.protected'))

        flash("Invalid username or password")
        return redirect(url_for('auth.login'))

    return render_template('login.html', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_pw = generate_password_hash(form.password.data)
        new_user = Users(
            username=form.username.data,
            email=form.email.data.lower(),
            password=hashed_pw
        )
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful! Please log in.")
        return redirect(url_for('auth.login'))

    return render_template('register.html', form=form)


@auth_bp.route('/protected')
@login_required
def protected():
    return render_template('landing.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))




# from flask import Blueprint, render_template, redirect, url_for, request, flash
# from flask_login import login_user, login_required, logout_user
# from werkzeug.security import generate_password_hash, check_password_hash
# from app.models.users import Users
# from app import db, limiter

# auth_bp = Blueprint('auth', __name__)

# @auth_bp.route('/login', methods=['GET', 'POST'])
# @limiter.limit("10 per minute")
# def login():
#     if request.method == 'POST':
#         username = request.form.get('username')
#         password = request.form.get('password')

#         user = Users.query.filter_by(username=username).first()

#         if user and check_password_hash(user.password, password):
#             login_user(user)
#             return redirect(url_for('auth.protected'))

#         flash("Invalid username or password")
#         return redirect(url_for('auth.login'))

#     return render_template('login.html')


# @auth_bp.route('/register', methods=['GET', 'POST'])
# @limiter.limit("10 per minute")
# def register():
#     if request.method == 'POST':
#         username = request.form.get('username')
#         email = request.form.get('email')
#         password = generate_password_hash(request.form.get('password'))

#         new_user = Users(username=username, email=email, password=password)
#         db.session.add(new_user)
#         db.session.commit()

#         return redirect(url_for('auth.login'))

#     return render_template('register.html')


# @auth_bp.route('/protected')
# @login_required
# def protected():
#     return render_template('landing.html')


# @auth_bp.route('/logout')
# @login_required
# def logout():
#     logout_user()
#     return redirect(url_for('auth.login'))
