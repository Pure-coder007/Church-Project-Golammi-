from flask import Flask, render_template, redirect, url_for, flash
from config import Config, DevelopmentConfig, ProductionConfig
from extensions import db, login_manager, migrate, csrf
from models.user import User
from routes.auth import auth_bp
from routes.admin import admin_bp
from models import User, Sermon, Event, BlogPost, GalleryImage, RadioStation, RadioSchedule, Testimony, PrayerRequest, ChurchStats, FinancialRecord, MemberGrowth
from routes.frontend import frontend_bp
from utils import get_current_time
import os


def create_app(config_class=DevelopmentConfig):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure upload directory exists
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    for subdir in [
        "sermons",
        "thumbnails",
        "events",
        "blog",
        "gallery",
        "radio",
        "testimonies",
    ]:
        os.makedirs(os.path.join(app.config["UPLOAD_FOLDER"], subdir), exist_ok=True)
        os.makedirs(
            os.path.join(app.config["UPLOAD_FOLDER"], "gallery", "thumbnails"),
            exist_ok=True,
        )

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"
    migrate.init_app(app, db)
    csrf.init_app(app)

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(frontend_bp)

    # User loader
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Context processors
    @app.context_processor
    def utility_processor():
        return {
            "get_current_time": get_current_time,
            "app_name": "GOLAMMI Worship Center",
        }

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template("frontend/404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template("frontend/500.html"), 500

    return app


# Create app instance
app = create_app(DevelopmentConfig)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
