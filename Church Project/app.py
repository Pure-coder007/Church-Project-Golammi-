from flask import Flask, render_template, redirect, url_for, flash, request, g, session
from config import Config, DevelopmentConfig, ProductionConfig
from extensions import db, login_manager, migrate, csrf
from models.user import User
from routes.auth import auth_bp
from routes.admin import admin_bp
from models import User, Sermon, Event, BlogPost, GalleryImage, RadioStation, RadioSchedule, Testimony, PrayerRequest, DonationSubmission, ActivityLog, ChurchStats, FinancialRecord, MemberGrowth
from routes.frontend import frontend_bp
from flask_login import current_user
from utils import get_current_time, media_url
import os
import hashlib
from datetime import datetime


def create_app(config_class=DevelopmentConfig):
    app = Flask(__name__)
    app.config.from_object(config_class)

    def should_log_request():
        if request.path.startswith("/static/"):
            return False
        if request.endpoint == "static":
            return False
        return True

    def build_activity_details(response_time_ms, status_code):
        endpoint = request.endpoint or "unknown"
        section = "admin" if request.path.startswith("/admin") else "frontend"
        clean_endpoint = endpoint.split(".")[-1].replace("_", " ").strip() or "page"
        action = clean_endpoint.title()
        if request.method == "GET":
            action_label = f"Viewed {action}"
        else:
            action_label = f"{request.method.title()} {action}"

        request_summary = (
            f"{request.method} request to {request.path} returned {status_code} in "
            f"{response_time_ms}ms"
        )
        return section, action_label, request_summary, endpoint

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
        return User.query.get(user_id)

    @app.before_request
    def capture_request_started_at():
        g.request_started_at = datetime.utcnow()

        if (
            request.path.startswith("/admin")
            and request.endpoint not in {"auth.login", "auth.logout", "auth.setup_super_admin"}
            and getattr(current_user, "is_authenticated", False)
        ):
            last_activity_raw = session.get("admin_last_activity")
            now = get_current_time()
            timeout_seconds = int(app.config["PERMANENT_SESSION_LIFETIME"].total_seconds())

            if last_activity_raw:
                try:
                    last_activity = datetime.fromisoformat(last_activity_raw)
                    if (now - last_activity).total_seconds() > timeout_seconds:
                        from flask_login import logout_user

                        logout_user()
                        session.clear()
                        flash(
                            "Your session is expired. Please log back in.",
                            "warning",
                        )
                        return redirect(url_for("auth.login", next=request.url))
                except ValueError:
                    session.pop("admin_last_activity", None)

            session.permanent = True
            session["admin_last_activity"] = now.isoformat()

    @app.after_request
    def apply_security_headers(response):
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        if not app.debug:
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "img-src 'self' data: https:; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com data:; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "connect-src 'self'; "
                "frame-ancestors 'self';"
            )

        if should_log_request():
            try:
                started_at = getattr(g, "request_started_at", datetime.utcnow())
                response_time_ms = max(
                    int((datetime.utcnow() - started_at).total_seconds() * 1000), 0
                )
                section, action_label, request_summary, endpoint = build_activity_details(
                    response_time_ms, response.status_code
                )
                forwarded_for = request.headers.get("X-Forwarded-For", "")
                ip_address = (
                    forwarded_for.split(",")[0].strip()
                    if forwarded_for
                    else (request.remote_addr or "unknown")
                )
                user_agent = request.user_agent.string[:500] if request.user_agent.string else None
                visitor_source = f"{ip_address}|{user_agent or 'unknown'}"
                visitor_key = hashlib.sha1(visitor_source.encode("utf-8")).hexdigest()
                user_id = current_user.id if getattr(current_user, "is_authenticated", False) else None

                with db.engine.begin() as connection:
                    connection.execute(
                        ActivityLog.__table__.insert().values(
                            method=request.method,
                            path=request.path[:500],
                            endpoint=endpoint[:200] if endpoint else None,
                            section=section,
                            action_label=action_label[:255],
                            request_summary=request_summary[:255],
                            status_code=response.status_code,
                            response_time_ms=response_time_ms,
                            ip_address=ip_address[:64] if ip_address else None,
                            visitor_key=visitor_key,
                            user_agent=user_agent,
                            referrer=request.referrer[:500] if request.referrer else None,
                            user_id=user_id,
                        )
                    )
            except Exception:
                pass
        return response

    # Context processors
    @app.context_processor
    def utility_processor():
        return {
            "get_current_time": get_current_time,
            "media_url": media_url,
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


def get_runtime_config():
    env_name = (os.environ.get("FLASK_ENV") or os.environ.get("APP_ENV") or "development").strip().lower()
    if env_name == "production":
        return ProductionConfig
    return DevelopmentConfig


# Create app instance
app = create_app(get_runtime_config())

if __name__ == "__main__":
    app.run(
        debug=app.config.get("DEBUG", False),
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
    )
