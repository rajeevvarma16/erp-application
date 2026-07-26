import click

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy import inspect, text

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'   # ✅ CRITICAL FIX
limiter = Limiter(key_func=get_remote_address)

def create_app():
    app = Flask(__name__)

    # Load config
    app.config.from_object('config.Config')

    # Init extensions
    db.init_app(app)
    login_manager.init_app(app)
    limiter.init_app(app)

    # This project uses SQLite without a migration framework. Upgrade an
    # existing users table so current installations can adopt RBAC safely.
    with app.app_context():
        inspector = inspect(db.engine)
        if "users" in inspector.get_table_names():
            columns = {column["name"] for column in inspector.get_columns("users")}
            if "role" not in columns:
                with db.engine.begin() as connection:
                    connection.execute(text(
                        "ALTER TABLE users ADD COLUMN role VARCHAR(20) "
                        "NOT NULL DEFAULT 'employee'"
                    ))

    # User loader
    from app.models.users import Users

    @login_manager.user_loader
    def load_user(user_id):
        return Users.query.get(int(user_id))

    # Register blueprints
    from app.routes.main_routes import main_bp
    from app.routes.auth_routes import auth_bp
    from app.routes.dashboard_routes import dashboard_bp
    from app.routes.employees_routes import employees_bp
    from app.routes.vendors_routes import vendors_bp
    from app.routes.customers_routes import customers_bp
    from app.routes.inventory_routes import inventory_bp
    from app.routes.chatbot_routes import chatbot_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(employees_bp)
    app.register_blueprint(vendors_bp)
    app.register_blueprint(customers_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(chatbot_bp)

    @app.context_processor
    def inject_permissions():
        from app.rbac import has_permission
        return {"can": lambda resource, action: has_permission(current_user, resource, action)}

    @app.cli.command("set-role")
    @click.argument("username")
    @click.argument("role", type=click.Choice(["admin", "manager", "employee"]))
    def set_role(username, role):
        """Assign an RBAC role: flask --app run set-role USERNAME ROLE."""
        user = Users.query.filter_by(username=username).first()
        if user is None:
            raise click.ClickException(f"User '{username}' was not found.")
        user.role = role
        db.session.commit()
        click.echo(f"Assigned {role} role to {username}.")

    return app
