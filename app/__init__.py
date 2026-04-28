from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Bu sayfaya erişmek için giriş yapmanız gerekiyor.'
    login_manager.login_message_category = 'warning'

    from app.routes.auth import auth_bp
    from app.routes.dietitian import dietitian_bp
    from app.routes.patient import patient_bp
    from app.routes.main import main_bp
    from app.routes.ai_assistant import ai_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dietitian_bp, url_prefix='/dietitian')
    app.register_blueprint(patient_bp, url_prefix='/patient')
    app.register_blueprint(ai_bp, url_prefix='/ai')
    app.register_blueprint(main_bp)

    # CSRF muafiyetlerini blueprint kaydından SONRA uygula
    from app.routes.dietitian import ai_assist, update_patient_notes, ai_generate_program
    csrf.exempt(ai_assist)
    csrf.exempt(update_patient_notes)
    csrf.exempt(ai_generate_program)

    # Error handlers
    from app.routes.errors import register_error_handlers
    register_error_handlers(app)

    # Context processors
    from datetime import datetime
    @app.context_processor
    def inject_now():
        return {'now': datetime.utcnow}

    return app
