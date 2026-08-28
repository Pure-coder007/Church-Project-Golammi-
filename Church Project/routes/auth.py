from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
    session,
)
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from models.user import User


def has_letters(value):
    return any(char.isalpha() for char in (value or ""))
from forms import LoginForm
from utils import get_current_time
from urllib.parse import urlparse, urljoin

auth_bp = Blueprint("auth", __name__)


def is_safe_redirect_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in {"http", "https"} and ref_url.netloc == test_url.netloc


@auth_bp.route("/admin/login", methods=["GET", "POST"])
def login():
    """Admin login page"""
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash("Your account has been deactivated.", "danger")
                return render_template("admin/login.html", form=form)

            login_user(user, remember=form.remember.data)
            session.permanent = True
            session["admin_last_activity"] = get_current_time().isoformat()
            user.last_login = get_current_time()
            db.session.commit()

            next_page = request.args.get("next")
            if next_page and is_safe_redirect_url(next_page):
                return redirect(next_page)
            return redirect(url_for("admin.dashboard"))
        else:
            flash("Invalid email or password.", "danger")

    return render_template("admin/login.html", form=form)


@auth_bp.route("/admin/logout")
@login_required
def logout():
    """Admin logout"""
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/admin/super-admin/setup", methods=["GET", "POST"])
def setup_super_admin():
    """Setup super admin (initial setup)"""
    # Check if super admin already exists
    if User.query.filter_by(role="super_admin").first():
        flash("Super admin already exists.", "warning")
        return redirect(url_for("auth.login"))

    form = LoginForm()
    if form.validate_on_submit():
        # Create super admin
        user = User(
            username="superadmin",
            email=form.email.data,
            full_name="Super Administrator",
            role="super_admin",
            is_active=True,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        flash("Super admin created successfully! Please login.", "success")
        return redirect(url_for("auth.login"))

    return render_template("admin/setup.html", form=form)


@auth_bp.route("/admin/profile", methods=["GET", "POST"])
@login_required
def profile():
    """Admin profile page"""
    user = current_user

    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        full_name = (request.form.get("full_name") or "").strip()
        email = (request.form.get("email") or "").strip()
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        if not username or not full_name or not email:
            flash("Username, full name, and email are required.", "danger")
            return redirect(url_for("auth.profile"))
        if not has_letters(full_name):
            flash("Full name must contain letters.", "danger")
            return redirect(url_for("auth.profile"))

        existing = User.query.filter(
            User.username == username, User.id != user.id
        ).first()
        if existing:
            flash("Username already taken.", "danger")
            return redirect(url_for("auth.profile"))

        existing = User.query.filter(User.email == email, User.id != user.id).first()
        if existing:
            flash("Email already registered.", "danger")
            return redirect(url_for("auth.profile"))

        user.username = username
        user.full_name = full_name
        user.email = email

        if current_password or new_password or confirm_password:
            if not user.is_super_admin():
                flash("Only the super admin can change passwords from the admin panel.", "danger")
                return redirect(url_for("auth.profile"))
            if not (current_password and new_password and confirm_password):
                flash("Complete all password fields to change your password.", "danger")
                return redirect(url_for("auth.profile"))
            if len(new_password) < 8:
                flash("New password must be at least 8 characters long.", "danger")
                return redirect(url_for("auth.profile"))
            if not user.check_password(current_password):
                flash("Current password is incorrect.", "danger")
                return redirect(url_for("auth.profile"))
            if new_password != confirm_password:
                flash("Passwords do not match.", "danger")
                return redirect(url_for("auth.profile"))
            user.set_password(new_password)

        db.session.commit()
        flash("Profile updated successfully!", "success")
        return redirect(url_for("auth.profile"))

    return render_template("admin/profile.html", user=user)
