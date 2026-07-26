from functools import wraps

from flask import abort
from flask_login import current_user, login_required


ROLES = ("admin", "manager", "employee")

# A permission is represented as (resource, action).  "*" grants every action.
ROLE_PERMISSIONS = {
    "admin": {("*", "*")},
    "manager": {
        ("inventory", "view"), ("inventory", "add"), ("inventory", "edit"),
        ("inventory", "delete"), ("inventory", "analytics"),
        ("vendors", "view"), ("vendors", "add"), ("vendors", "edit"),
        ("vendors", "delete"), ("vendors", "analytics"),
        ("employees", "view"),
        ("customers", "view"),
    },
    "employee": {
        ("employees", "view"), ("employees", "add"), ("employees", "edit"),
        ("customers", "view"), ("customers", "add"), ("customers", "edit"),
    },
}


def has_permission(user, resource, action):
    """Return whether a logged-in user may perform an action."""
    if not getattr(user, "is_authenticated", False):
        return False

    permissions = ROLE_PERMISSIONS.get(getattr(user, "role", "employee"), set())
    return ("*", "*") in permissions or (resource, action) in permissions


def permission_required(resource, action):
    """Require login and a named RBAC permission for a view."""
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            if not has_permission(current_user, resource, action):
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorator
