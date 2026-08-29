from flask import Blueprint, flash, redirect, render_template, request, url_for
from werkzeug.security import generate_password_hash

from app import db
from app.models.users import Users
from app.rbac import ROLES, permission_required


users_bp = Blueprint('users', __name__)


def _user_form_values():
    """Return normalized values submitted by the user-management forms."""
    return {
        "username": request.form.get("username", "").strip(),
        "email": request.form.get("email", "").strip().lower(),
        "role": request.form.get("role", "employee"),
    }


def _validate_user_values(values, user_id=None):
    if not values["username"] or not values["email"]:
        return "Username and email are required."
    if values["role"] not in ROLES:
        return "Please select a valid role."

    username_query = Users.query.filter_by(username=values["username"])
    email_query = Users.query.filter_by(email=values["email"])
    if user_id is not None:
        username_query = username_query.filter(Users.id != user_id)
        email_query = email_query.filter(Users.id != user_id)

    if username_query.first():
        return "Username already exists."
    if email_query.first():
        return "Email already exists."
    return None


@users_bp.route('/users')
@permission_required('users', 'view')
def users():
    return render_template('users.html', users=Users.query.order_by(Users.id).all())


@users_bp.route('/users/add', methods=['GET', 'POST'])
@permission_required('users', 'add')
def add_user():
    if request.method == 'POST':
        values = _user_form_values()
        password = request.form.get("password", "")
        error = _validate_user_values(values)
        if not password:
            error = error or "Password is required."

        if error:
            flash(error)
            return render_template('add_user.html', roles=ROLES, values=values)

        db.session.add(Users(
            username=values["username"],
            email=values["email"],
            password=generate_password_hash(password, method='pbkdf2:sha256'),
            role=values["role"],
        ))
        db.session.commit()
        flash("User added successfully.")
        return redirect(url_for('users.users'))

    return render_template('add_user.html', roles=ROLES, values={})


@users_bp.route('/users/edit/<int:id>', methods=['GET', 'POST'])
@permission_required('users', 'edit')
def edit_user(id):
    user = Users.query.get_or_404(id)

    if request.method == 'POST':
        values = _user_form_values()
        error = _validate_user_values(values, user.id)
        if error:
            flash(error)
            return render_template('edit_user.html', user=user, roles=ROLES, values=values)

        user.username = values["username"]
        user.email = values["email"]
        user.role = values["role"]
        password = request.form.get("password", "")
        if password:
            user.password = generate_password_hash(password, method='pbkdf2:sha256')

        db.session.commit()
        flash("User updated successfully.")
        return redirect(url_for('users.users'))

    return render_template('edit_user.html', user=user, roles=ROLES, values=None)


@users_bp.route('/users/delete/<int:id>', methods=['POST'])
@permission_required('users', 'delete')
def delete_user(id):
    user = Users.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    flash("User deleted successfully.")
    return redirect(url_for('users.users'))
