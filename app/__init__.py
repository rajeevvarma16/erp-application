from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

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

    return app
