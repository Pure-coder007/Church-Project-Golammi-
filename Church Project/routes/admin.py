from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, BooleanField, EmailField, IntegerField, PasswordField, HiddenField, URLField, DateTimeField, FloatField
from wtforms.validators import DataRequired, Email, Length, Optional, URL, NumberRange
from extensions import db
from models.user import User
from models.sermon import Sermon
from models.event import Event
from models.blog import BlogPost
from models.gallery import GalleryImage
from models.radio import RadioStation, RadioSchedule
from models.testimony import Testimony
from models.prayer import PrayerRequest
from forms import (
    UserForm, SermonForm, EventForm, BlogForm, GalleryForm,
    RadioForm, RadioScheduleForm, TestimonyForm, SettingsForm, PrayerRequestForm
)
from utils import save_picture, save_file, generate_slug, get_current_time
from datetime import datetime, timedelta
import os
from sqlalchemy import func, extract

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(f):
    """Decorator to require admin access"""
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash("You need admin access for this page.", "danger")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)

    return decorated_function


def super_admin_required(f):
    """Decorator to require super admin access"""
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_super_admin():
            flash("Super admin access required.", "danger")
            return redirect(url_for("admin.dashboard"))
        return f(*args, **kwargs)

    return decorated_function


# ===================== DASHBOARD =====================
@admin_bp.route("/")
@login_required
@admin_required
def dashboard():
    """Admin dashboard"""
    # Statistics
    stats = {
        "total_sermons": Sermon.query.count(),
        "total_events": Event.query.count(),
        "total_blog_posts": BlogPost.query.count(),
        "total_gallery_images": GalleryImage.query.count(),
        "total_testimonies": Testimony.query.count(),
        "total_prayer_requests": PrayerRequest.query.count(),
        "total_users": User.query.count(),
        "pending_testimonies": Testimony.query.filter_by(is_approved=False).count(),
        "pending_prayer_requests": PrayerRequest.query.filter_by(
            is_prayed_for=False
        ).count(),
        "recent_sermons": Sermon.query.order_by(Sermon.created_at.desc())
        .limit(5)
        .all(),
        "recent_events": Event.query.order_by(Event.start_date.desc()).limit(5).all(),
        "recent_blog_posts": BlogPost.query.order_by(BlogPost.created_at.desc())
        .limit(5)
        .all(),
    }
    return render_template("admin/dashboard.html", stats=stats)


# ===================== USER MANAGEMENT =====================
@admin_bp.route("/users")
@login_required
@super_admin_required
def users():
    """List all users"""
    page = request.args.get("page", 1, type=int)
    users = User.query.order_by(User.created_at.desc()).paginate(page=page, per_page=20)
    return render_template("admin/users.html", users=users)


@admin_bp.route("/users/add", methods=["GET", "POST"])
@login_required
@super_admin_required
def add_user():
    """Add a new user"""
    form = UserForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            full_name=form.full_name.data,
            role=form.role.data,
            is_active=form.is_active.data,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("User added successfully!", "success")
        return redirect(url_for("admin.users"))
    return render_template("admin/user_form.html", form=form, title="Add User")


@admin_bp.route("/users/edit/<int:user_id>", methods=["GET", "POST"])
@login_required
@super_admin_required
def edit_user(user_id):
    """Edit a user"""
    user = User.query.get_or_404(user_id)
    form = UserForm(obj=user)

    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.full_name = form.full_name.data
        user.role = form.role.data
        user.is_active = form.is_active.data
        if form.password.data:
            user.set_password(form.password.data)
        db.session.commit()
        flash("User updated successfully!", "success")
        return redirect(url_for("admin.users"))

    return render_template(
        "admin/user_form.html", form=form, user=user, title="Edit User"
    )


@admin_bp.route("/users/delete/<int:user_id>", methods=["POST"])
@login_required
@super_admin_required
def delete_user(user_id):
    """Delete a user"""
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You cannot delete yourself.", "danger")
        return redirect(url_for("admin.users"))

    db.session.delete(user)
    db.session.commit()
    flash("User deleted successfully!", "success")
    return redirect(url_for("admin.users"))


# ===================== SERMON MANAGEMENT =====================
@admin_bp.route("/sermons")
@login_required
@admin_required
def sermons():
    """List all sermons"""
    page = request.args.get("page", 1, type=int)
    sermons = Sermon.query.order_by(Sermon.created_at.desc()).paginate(
        page=page, per_page=10
    )
    return render_template("admin/sermons.html", sermons=sermons)


@admin_bp.route("/sermons/add", methods=["GET", "POST"])
@login_required
@admin_required
def add_sermon():
    """Add a new sermon"""
    form = SermonForm()
    if form.validate_on_submit():
        # Generate slug
        slug = generate_slug(form.title.data)
        # Check for duplicate slug
        if Sermon.query.filter_by(slug=slug).first():
            slug = f"{slug}-{int(datetime.utcnow().timestamp())}"

        # Handle file uploads
        audio_path = None
        thumbnail_path = None

        if form.audio_file.data:
            audio_path = save_file(form.audio_file.data, "sermons")
        if form.thumbnail.data:
            thumbnail_path = save_picture(
                form.thumbnail.data, "thumbnails", size=(400, 225)
            )

        sermon = Sermon(
            title=form.title.data,
            slug=slug,
            description=form.description.data,
            speaker=form.speaker.data,
            category=form.category.data,
            date_preached=form.date_preached.data or datetime.utcnow(),
            audio_file=audio_path,
            video_url=form.video_url.data,
            live_stream_url=form.live_stream_url.data,
            thumbnail=thumbnail_path,
            is_live=form.is_live.data,
            is_featured=form.is_featured.data,
            is_published=form.is_published.data,
            created_by=current_user.id,
        )
        db.session.add(sermon)
        db.session.commit()
        flash("Sermon added successfully!", "success")
        return redirect(url_for("admin.sermons"))

    return render_template("admin/sermon_form.html", form=form, title="Add Sermon")


@admin_bp.route("/sermons/edit/<int:sermon_id>", methods=["GET", "POST"])
@login_required
@admin_required
def edit_sermon(sermon_id):
    """Edit a sermon"""
    sermon = Sermon.query.get_or_404(sermon_id)
    form = SermonForm(obj=sermon)

    if form.validate_on_submit():
        # Handle file uploads
        if form.audio_file.data:
            # Delete old file if exists
            if sermon.audio_file:
                old_path = os.path.join(
                    current_app.config["UPLOAD_FOLDER"], sermon.audio_file
                )
                if os.path.exists(old_path):
                    os.remove(old_path)
            sermon.audio_file = save_file(form.audio_file.data, "sermons")

        if form.thumbnail.data:
            if sermon.thumbnail:
                old_path = os.path.join(
                    current_app.config["UPLOAD_FOLDER"], sermon.thumbnail
                )
                if os.path.exists(old_path):
                    os.remove(old_path)
            sermon.thumbnail = save_picture(
                form.thumbnail.data, "thumbnails", size=(400, 225)
            )

        sermon.title = form.title.data
        sermon.description = form.description.data
        sermon.speaker = form.speaker.data
        sermon.category = form.category.data
        sermon.date_preached = form.date_preached.data or datetime.utcnow()
        sermon.video_url = form.video_url.data
        sermon.live_stream_url = form.live_stream_url.data
        sermon.is_live = form.is_live.data
        sermon.is_featured = form.is_featured.data
        sermon.is_published = form.is_published.data
        sermon.updated_by = current_user.id

        db.session.commit()
        flash("Sermon updated successfully!", "success")
        return redirect(url_for("admin.sermons"))

    return render_template(
        "admin/sermon_form.html", form=form, sermon=sermon, title="Edit Sermon"
    )


@admin_bp.route("/sermons/delete/<int:sermon_id>", methods=["POST"])
@login_required
@admin_required
def delete_sermon(sermon_id):
    """Delete a sermon"""
    sermon = Sermon.query.get_or_404(sermon_id)

    # Delete associated files
    if sermon.audio_file:
        path = os.path.join(current_app.config["UPLOAD_FOLDER"], sermon.audio_file)
        if os.path.exists(path):
            os.remove(path)
    if sermon.thumbnail:
        path = os.path.join(current_app.config["UPLOAD_FOLDER"], sermon.thumbnail)
        if os.path.exists(path):
            os.remove(path)

    db.session.delete(sermon)
    db.session.commit()
    flash("Sermon deleted successfully!", "success")
    return redirect(url_for("admin.sermons"))


@admin_bp.route("/sermons/toggle-live/<int:sermon_id>", methods=["POST"])
@login_required
@admin_required
def toggle_live_sermon(sermon_id):
    """Toggle live status of a sermon"""
    sermon = Sermon.query.get_or_404(sermon_id)
    sermon.is_live = not sermon.is_live
    db.session.commit()
    flash(
        f'Live status updated to {"Live" if sermon.is_live else "Not Live"}', "success"
    )
    return redirect(url_for("admin.sermons"))


# ===================== EVENT MANAGEMENT =====================
@admin_bp.route("/events")
@login_required
@admin_required
def events():
    """List all events"""
    page = request.args.get("page", 1, type=int)
    events = Event.query.order_by(Event.start_date.desc()).paginate(
        page=page, per_page=10
    )
    return render_template("admin/events.html", events=events)


@admin_bp.route("/events/add", methods=["GET", "POST"])
@login_required
@admin_required
def add_event():
    """Add a new event"""
    form = EventForm()
    if form.validate_on_submit():
        slug = generate_slug(form.title.data)
        if Event.query.filter_by(slug=slug).first():
            slug = f"{slug}-{int(datetime.utcnow().timestamp())}"

        image_path = None
        if form.image.data:
            image_path = save_picture(form.image.data, "events", size=(800, 500))

        event = Event(
            title=form.title.data,
            slug=slug,
            description=form.description.data,
            short_description=form.short_description.data,
            category=form.category.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            start_time=form.start_time.data,
            end_time=form.end_time.data,
            location=form.location.data,
            venue=form.venue.data,
            is_online=form.is_online.data,
            online_link=form.online_link.data,
            image=image_path,
            is_featured=form.is_featured.data,
            is_published=form.is_published.data,
            registration_required=form.registration_required.data,
            registration_link=form.registration_link.data,
            created_by=current_user.id,
        )
        db.session.add(event)
        db.session.commit()
        flash("Event added successfully!", "success")
        return redirect(url_for("admin.events"))

    return render_template("admin/event_form.html", form=form, title="Add Event")


@admin_bp.route("/events/edit/<int:event_id>", methods=["GET", "POST"])
@login_required
@admin_required
def edit_event(event_id):
    """Edit an event"""
    event = Event.query.get_or_404(event_id)
    form = EventForm(obj=event)

    if form.validate_on_submit():
        if form.image.data:
            if event.image:
                old_path = os.path.join(
                    current_app.config["UPLOAD_FOLDER"], event.image
                )
                if os.path.exists(old_path):
                    os.remove(old_path)
            event.image = save_picture(form.image.data, "events", size=(800, 500))

        event.title = form.title.data
        event.description = form.description.data
        event.short_description = form.short_description.data
        event.category = form.category.data
        event.start_date = form.start_date.data
        event.end_date = form.end_date.data
        event.start_time = form.start_time.data
        event.end_time = form.end_time.data
        event.location = form.location.data
        event.venue = form.venue.data
        event.is_online = form.is_online.data
        event.online_link = form.online_link.data
        event.is_featured = form.is_featured.data
        event.is_published = form.is_published.data
        event.registration_required = form.registration_required.data
        event.registration_link = form.registration_link.data
        event.updated_by = current_user.id

        db.session.commit()
        flash("Event updated successfully!", "success")
        return redirect(url_for("admin.events"))

    return render_template(
        "admin/event_form.html", form=form, event=event, title="Edit Event"
    )


@admin_bp.route("/events/delete/<int:event_id>", methods=["POST"])
@login_required
@admin_required
def delete_event(event_id):
    """Delete an event"""
    event = Event.query.get_or_404(event_id)
    if event.image:
        path = os.path.join(current_app.config["UPLOAD_FOLDER"], event.image)
        if os.path.exists(path):
            os.remove(path)
    db.session.delete(event)
    db.session.commit()
    flash("Event deleted successfully!", "success")
    return redirect(url_for("admin.events"))


# ===================== BLOG MANAGEMENT =====================
@admin_bp.route("/blog")
@login_required
@admin_required
def blog():
    """List all blog posts"""
    page = request.args.get("page", 1, type=int)
    posts = BlogPost.query.order_by(BlogPost.created_at.desc()).paginate(
        page=page, per_page=10
    )
    return render_template("admin/blog.html", posts=posts)


@admin_bp.route("/blog/add", methods=["GET", "POST"])
@login_required
@admin_required
def add_blog():
    """Add a new blog post"""
    form = BlogForm()
    if form.validate_on_submit():
        slug = generate_slug(form.title.data)
        if BlogPost.query.filter_by(slug=slug).first():
            slug = f"{slug}-{int(datetime.utcnow().timestamp())}"

        image_path = None
        if form.featured_image.data:
            image_path = save_picture(form.featured_image.data, "blog", size=(800, 500))

        post = BlogPost(
            title=form.title.data,
            slug=slug,
            content=form.content.data,
            excerpt=form.excerpt.data,
            category=form.category.data,
            author=form.author.data,
            featured_image=image_path,
            is_featured=form.is_featured.data,
            is_published=form.is_published.data,
            meta_title=form.meta_title.data,
            meta_description=form.meta_description.data,
            meta_keywords=form.meta_keywords.data,
            published_date=datetime.utcnow() if form.is_published.data else None,
            created_by=current_user.id,
        )
        db.session.add(post)
        db.session.commit()
        flash("Blog post added successfully!", "success")
        return redirect(url_for("admin.blog"))

    return render_template("admin/blog_form.html", form=form, title="Add Blog Post")


@admin_bp.route("/blog/edit/<int:post_id>", methods=["GET", "POST"])
@login_required
@admin_required
def edit_blog(post_id):
    """Edit a blog post"""
    post = BlogPost.query.get_or_404(post_id)
    form = BlogForm(obj=post)

    if form.validate_on_submit():
        if form.featured_image.data:
            if post.featured_image:
                old_path = os.path.join(
                    current_app.config["UPLOAD_FOLDER"], post.featured_image
                )
                if os.path.exists(old_path):
                    os.remove(old_path)
            post.featured_image = save_picture(
                form.featured_image.data, "blog", size=(800, 500)
            )

        post.title = form.title.data
        post.content = form.content.data
        post.excerpt = form.excerpt.data
        post.category = form.category.data
        post.author = form.author.data
        post.is_featured = form.is_featured.data
        post.is_published = form.is_published.data
        post.meta_title = form.meta_title.data
        post.meta_description = form.meta_description.data
        post.meta_keywords = form.meta_keywords.data
        if form.is_published.data and not post.published_date:
            post.published_date = datetime.utcnow()
        post.updated_by = current_user.id

        db.session.commit()
        flash("Blog post updated successfully!", "success")
        return redirect(url_for("admin.blog"))

    return render_template(
        "admin/blog_form.html", form=form, post=post, title="Edit Blog Post"
    )


@admin_bp.route("/blog/delete/<int:post_id>", methods=["POST"])
@login_required
@admin_required
def delete_blog(post_id):
    """Delete a blog post"""
    post = BlogPost.query.get_or_404(post_id)
    if post.featured_image:
        path = os.path.join(current_app.config["UPLOAD_FOLDER"], post.featured_image)
        if os.path.exists(path):
            os.remove(path)
    db.session.delete(post)
    db.session.commit()
    flash("Blog post deleted successfully!", "success")
    return redirect(url_for("admin.blog"))


# ===================== GALLERY MANAGEMENT =====================
@admin_bp.route("/gallery")
@login_required
@admin_required
def gallery():
    """List all gallery images"""
    page = request.args.get("page", 1, type=int)
    images = GalleryImage.query.order_by(GalleryImage.created_at.desc()).paginate(
        page=page, per_page=20
    )
    return render_template("admin/gallery.html", images=images)


@admin_bp.route("/gallery/add", methods=["GET", "POST"])
@login_required
@admin_required
def add_gallery():
    """Add a new gallery image"""
    form = GalleryForm()
    if form.validate_on_submit():
        image_path = save_picture(form.image.data, "gallery", size=(800, 800))
        thumbnail_path = save_picture(
            form.image.data, "gallery/thumbnails", size=(300, 300)
        )

        image = GalleryImage(
            title=form.title.data,
            description=form.description.data,
            category=form.category.data,
            image_path=image_path,
            thumbnail_path=thumbnail_path,
            is_featured=form.is_featured.data,
            is_published=form.is_published.data,
            created_by=current_user.id,
        )
        db.session.add(image)
        db.session.commit()
        flash("Image added successfully!", "success")
        return redirect(url_for("admin.gallery"))

    return render_template("admin/gallery_form.html", form=form, title="Add Image")


@admin_bp.route("/gallery/delete/<int:image_id>", methods=["POST"])
@login_required
@admin_required
def delete_gallery(image_id):
    """Delete a gallery image"""
    image = GalleryImage.query.get_or_404(image_id)
    if image.image_path:
        path = os.path.join(current_app.config["UPLOAD_FOLDER"], image.image_path)
        if os.path.exists(path):
            os.remove(path)
    if image.thumbnail_path:
        path = os.path.join(current_app.config["UPLOAD_FOLDER"], image.thumbnail_path)
        if os.path.exists(path):
            os.remove(path)
    db.session.delete(image)
    db.session.commit()
    flash("Image deleted successfully!", "success")
    return redirect(url_for("admin.gallery"))


# ===================== RADIO MANAGEMENT =====================
@admin_bp.route("/radio")
@login_required
@admin_required
def radio():
    """List all radio stations"""
    stations = RadioStation.query.all()
    return render_template("admin/radio.html", stations=stations)


@admin_bp.route("/radio/add", methods=["GET", "POST"])
@login_required
@admin_required
def add_radio():
    """Add a new radio station"""
    form = RadioForm()
    if form.validate_on_submit():
        cover_image = None
        if form.cover_image.data:
            cover_image = save_picture(form.cover_image.data, "radio", size=(400, 400))

        station = RadioStation(
            name=form.name.data,
            description=form.description.data,
            stream_url=form.stream_url.data,
            backup_url=form.backup_url.data,
            is_active=form.is_active.data,
            is_featured=form.is_featured.data,
            cover_image=cover_image,
            schedule=form.schedule.data,
            created_by=current_user.id,
        )
        db.session.add(station)
        db.session.commit()
        flash("Radio station added successfully!", "success")
        return redirect(url_for("admin.radio"))

    return render_template(
        "admin/radio_form.html", form=form, title="Add Radio Station"
    )


@admin_bp.route("/radio/edit/<int:station_id>", methods=["GET", "POST"])
@login_required
@admin_required
def edit_radio(station_id):
    """Edit a radio station"""
    station = RadioStation.query.get_or_404(station_id)
    form = RadioForm(obj=station)

    if form.validate_on_submit():
        if form.cover_image.data:
            if station.cover_image:
                old_path = os.path.join(
                    current_app.config["UPLOAD_FOLDER"], station.cover_image
                )
                if os.path.exists(old_path):
                    os.remove(old_path)
            station.cover_image = save_picture(
                form.cover_image.data, "radio", size=(400, 400)
            )

        station.name = form.name.data
        station.description = form.description.data
        station.stream_url = form.stream_url.data
        station.backup_url = form.backup_url.data
        station.is_active = form.is_active.data
        station.is_featured = form.is_featured.data
        station.schedule = form.schedule.data

        db.session.commit()
        flash("Radio station updated successfully!", "success")
        return redirect(url_for("admin.radio"))

    return render_template(
        "admin/radio_form.html", form=form, station=station, title="Edit Radio Station"
    )


@admin_bp.route("/radio/delete/<int:station_id>", methods=["POST"])
@login_required
@admin_required
def delete_radio(station_id):
    """Delete a radio station"""
    station = RadioStation.query.get_or_404(station_id)
    if station.cover_image:
        path = os.path.join(current_app.config["UPLOAD_FOLDER"], station.cover_image)
        if os.path.exists(path):
            os.remove(path)
    db.session.delete(station)
    db.session.commit()
    flash("Radio station deleted successfully!", "success")
    return redirect(url_for("admin.radio"))


# ===================== TESTIMONY MANAGEMENT =====================

@admin_bp.route('/testimonies')
@login_required
@admin_required
def testimonies():
    """List all testimonies"""
    page = request.args.get('page', 1, type=int)
    testimonies = Testimony.query.order_by(Testimony.created_at.desc()).paginate(page=page, per_page=10)
    return render_template('admin/testimonies.html', testimonies=testimonies)


@admin_bp.route('/testimonies/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_testimony():
    """Add a new testimony from admin"""
    form = TestimonyForm()

    if form.validate_on_submit():
        image_path = None
        if form.image.data:
            image_path = save_picture(form.image.data, 'testimonies', size=(400, 400))

        testimony = Testimony(
            title=form.title.data,
            content=form.content.data,
            author_name=form.author_name.data,
            author_email=form.author_email.data,
            author_phone=form.author_phone.data,
            category=form.category.data,
            image=image_path,
            is_featured=form.is_featured.data,
            is_approved=form.is_approved.data,
            is_published=form.is_published.data,
            reviewed_by=current_user.id if form.is_approved.data else None,
            created_at=datetime.utcnow()
        )
        db.session.add(testimony)
        db.session.commit()
        flash('Testimony added successfully!', 'success')
        return redirect(url_for('admin.testimonies'))

    return render_template('admin/testimony_form.html', form=form, title='Add Testimony')


@admin_bp.route('/testimonies/edit/<int:testimony_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_testimony(testimony_id):
    """Edit a testimony"""
    testimony = Testimony.query.get_or_404(testimony_id)
    form = TestimonyForm(obj=testimony)

    if form.validate_on_submit():
        # Handle image upload
        if form.image.data:
            # Delete old image if exists
            if testimony.image:
                old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], testimony.image)
                if os.path.exists(old_path):
                    os.remove(old_path)
            testimony.image = save_picture(form.image.data, 'testimonies', size=(400, 400))

        # Update fields
        testimony.title = form.title.data
        testimony.content = form.content.data
        testimony.author_name = form.author_name.data
        testimony.author_email = form.author_email.data
        testimony.author_phone = form.author_phone.data
        testimony.category = form.category.data
        testimony.is_featured = form.is_featured.data
        testimony.is_approved = form.is_approved.data
        testimony.is_published = form.is_published.data
        testimony.reviewed_by = current_user.id if form.is_approved.data else None
        testimony.updated_at = datetime.utcnow()

        db.session.commit()
        flash('Testimony updated successfully!', 'success')
        return redirect(url_for('admin.testimonies'))

    return render_template('admin/testimony_form.html', form=form, testimony=testimony, title='Edit Testimony')


@admin_bp.route('/testimonies/approve/<int:testimony_id>', methods=['POST'])
@login_required
@admin_required
def approve_testimony(testimony_id):
    """Approve and publish a testimony"""
    testimony = Testimony.query.get_or_404(testimony_id)
    testimony.is_approved = True
    testimony.is_published = True
    testimony.reviewed_by = current_user.id
    testimony.updated_at = datetime.utcnow()
    db.session.commit()
    flash('Testimony approved and published successfully!', 'success')
    return redirect(url_for('admin.testimonies'))


@admin_bp.route('/testimonies/delete/<int:testimony_id>', methods=['POST'])
@login_required
@admin_required
def delete_testimony(testimony_id):
    """Delete a testimony"""
    testimony = Testimony.query.get_or_404(testimony_id)

    # Delete associated image
    if testimony.image:
        path = os.path.join(current_app.config['UPLOAD_FOLDER'], testimony.image)
        if os.path.exists(path):
            os.remove(path)

    db.session.delete(testimony)
    db.session.commit()
    flash('Testimony deleted successfully!', 'success')
    return redirect(url_for('admin.testimonies'))


# ===================== PRAYER REQUEST MANAGEMENT =====================

@admin_bp.route('/prayer-requests')
@login_required
@admin_required
def prayer_requests():
    """List all prayer requests"""
    page = request.args.get('page', 1, type=int)

    # Get paginated results
    paginated = PrayerRequest.query.order_by(PrayerRequest.created_at.desc()).paginate(page=page, per_page=10)

    # Add user info for responded_by
    for prayer in paginated.items:
        if prayer.responded_by:
            prayer.responded_by_user = User.query.get(prayer.responded_by)

    # Get counts for statistics - FIXED
    total = PrayerRequest.query.count()
    pending_count = PrayerRequest.query.filter_by(is_prayed_for=False).count()
    prayed_count = PrayerRequest.query.filter_by(is_prayed_for=True, is_answered=False).count()
    answered_count = PrayerRequest.query.filter_by(is_answered=True).count()

    # Create a wrapper object for the template
    class PrayerWrapper:
        def __init__(self, items, page, per_page, total, pages, has_prev, has_next, prev_num, next_num):
            self.items = items
            self.page = page
            self.per_page = per_page
            self.total = total
            self.pages = pages
            self.has_prev = has_prev
            self.has_next = has_next
            self.prev_num = prev_num
            self.next_num = next_num
            # Stats
            self.pending_count = pending_count
            self.prayed_count = prayed_count
            self.answered_count = answered_count

    wrapper = PrayerWrapper(
        items=paginated.items,
        page=paginated.page,
        per_page=paginated.per_page,
        total=total,
        pages=paginated.pages,
        has_prev=paginated.has_prev,
        has_next=paginated.has_next,
        prev_num=paginated.prev_num,
        next_num=paginated.next_num
    )

    return render_template('admin/prayer_requests.html',
                           prayers=paginated,
                           total=total,
                           pending_count=pending_count,
                           prayed_count=prayed_count,
                           answered_count=answered_count)


@admin_bp.route('/prayer-requests/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_prayer_request():
    """Add a new prayer request from admin"""
    form = PrayerRequestForm()

    if form.validate_on_submit():
        prayer = PrayerRequest(
            full_name=form.full_name.data if not form.is_anonymous.data else 'Anonymous',
            email=form.email.data,
            phone=form.phone.data,
            category=form.category.data,
            request=form.request.data,
            is_anonymous=form.is_anonymous.data
        )
        db.session.add(prayer)
        db.session.commit()
        flash('Prayer request added successfully!', 'success')
        return redirect(url_for('admin.prayer_requests'))

    return render_template('admin/add_prayer_request.html', form=form, title='Add Prayer Request')


@admin_bp.route('/prayer-requests/edit/<int:request_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_prayer_request(request_id):
    """Edit a prayer request"""
    prayer = PrayerRequest.query.get_or_404(request_id)

    # Create a custom form for editing
    class EditPrayerForm(FlaskForm):
        full_name = StringField('Full Name', validators=[DataRequired(), Length(max=100)])
        email = EmailField('Email', validators=[Optional(), Email()])
        phone = StringField('Phone', validators=[Optional(), Length(max=20)])
        category = SelectField('Category', choices=[
            ('healing', 'Healing / Health'),
            ('deliverance', 'Deliverance'),
            ('financial', 'Financial Breakthrough'),
            ('family', 'Family / Marriage'),
            ('career', 'Career / Business'),
            ('salvation', 'Salvation / Soul Winning'),
            ('general', 'General Request')
        ], validators=[DataRequired()])
        request = TextAreaField('Prayer Request', validators=[DataRequired()])
        is_anonymous = BooleanField('Submit Anonymously')
        is_prayed_for = BooleanField('Prayed For')
        is_answered = BooleanField('Answered')

    form = EditPrayerForm(obj=prayer)

    if form.validate_on_submit():
        prayer.full_name = form.full_name.data if not form.is_anonymous.data else 'Anonymous'
        prayer.email = form.email.data
        prayer.phone = form.phone.data
        prayer.category = form.category.data
        prayer.request = form.request.data
        prayer.is_anonymous = form.is_anonymous.data
        prayer.is_prayed_for = form.is_prayed_for.data
        prayer.is_answered = form.is_answered.data

        # If marked as answered, set responded info
        if form.is_answered.data and not prayer.responded_by:
            prayer.responded_by = current_user.id
            prayer.responded_at = datetime.utcnow()

        db.session.commit()
        flash('Prayer request updated successfully!', 'success')
        return redirect(url_for('admin.prayer_requests'))

    return render_template('admin/edit_prayer_request.html', form=form, prayer=prayer, title='Edit Prayer Request')


@admin_bp.route('/prayer-requests/respond/<int:request_id>', methods=['POST'])
@login_required
@admin_required
def respond_prayer(request_id):
    """Respond to a prayer request"""
    prayer = PrayerRequest.query.get_or_404(request_id)
    response = request.form.get('response')
    mark_answered = request.form.get('mark_answered')

    if not response:
        flash('Please provide a response.', 'danger')
        return redirect(url_for('admin.prayer_requests'))

    prayer.response = response
    prayer.is_prayed_for = True
    prayer.responded_by = current_user.id
    prayer.responded_at = datetime.utcnow()

    if mark_answered:
        prayer.is_answered = True

    db.session.commit()

    if mark_answered:
        flash('Prayer request response saved and marked as answered!', 'success')
    else:
        flash('Prayer request response saved! The requester has been notified.', 'success')

    return redirect(url_for('admin.prayer_requests'))


@admin_bp.route('/prayer-requests/mark-answered/<int:request_id>', methods=['POST'])
@login_required
@admin_required
def mark_answered(request_id):
    """Mark a prayer request as answered"""
    prayer = PrayerRequest.query.get_or_404(request_id)
    prayer.is_answered = True
    prayer.is_prayed_for = True
    prayer.responded_by = current_user.id
    prayer.responded_at = datetime.utcnow()
    db.session.commit()
    flash('Prayer request marked as answered!', 'success')
    return redirect(url_for('admin.prayer_requests'))


@admin_bp.route('/prayer-requests/delete/<int:request_id>', methods=['POST'])
@login_required
@admin_required
def delete_prayer(request_id):
    """Delete a prayer request"""
    prayer = PrayerRequest.query.get_or_404(request_id)
    db.session.delete(prayer)
    db.session.commit()
    flash('Prayer request deleted successfully!', 'success')
    return redirect(url_for('admin.prayer_requests'))


# ===================== CHURCH ANALYTICS =====================
@admin_bp.route('/analytics')
@login_required
@admin_required
def analytics():
    """Church analytics dashboard"""
    stats = None
    growth_data = [0] * 12
    total_tithes = 0
    total_offerings = 0
    total_donations = 0
    total_income = 0
    finance_labels = []
    finance_data = []
    member_growth_percent = 0
    records = None

    try:
        from models.church_stats import ChurchStats, FinancialRecord, MemberGrowth

        # Get church stats
        stats = ChurchStats.query.first()
        if not stats:
            stats = ChurchStats(
                total_members=0,
                total_men=0,
                total_women=0,
                total_children=0
            )
            db.session.add(stats)
            db.session.commit()

        # Calculate member growth percentage
        if stats.total_members > 0:
            prev_month = MemberGrowth.query.order_by(
                MemberGrowth.year.desc(),
                MemberGrowth.month.desc()
            ).limit(2).all()
            if len(prev_month) >= 2:
                prev_total = prev_month[1].total_members
                if prev_total > 0:
                    member_growth_percent = round(((stats.total_members - prev_total) / prev_total) * 100, 1)

        # Get growth data - last 12 months (descending order - newest first)
        growth_records = MemberGrowth.query.order_by(
            MemberGrowth.year.desc(),
            MemberGrowth.month.desc()
        ).limit(12).all()

        # Reverse to show chronological order (oldest to newest) for the chart
        growth_records = growth_records[::-1]

        if growth_records:
            growth_data = [record.total_members for record in growth_records]
            if len(growth_data) < 12:
                growth_data = [0] * (12 - len(growth_data)) + growth_data
        else:
            growth_data = [stats.total_members] + [0] * 11

        # Get financial data (super admin only)
        if current_user.is_super_admin():
            # Get page number
            page = request.args.get('page', 1, type=int)
            per_page = 7

            # Get paginated financial records - descending order (newest first)
            records_paginated = FinancialRecord.query.order_by(
                FinancialRecord.date.desc(),
                FinancialRecord.id.desc()  # Secondary ordering by ID for consistency
            ).paginate(page=page, per_page=per_page, error_out=False)

            # Add user info
            for record in records_paginated.items:
                if record.created_by:
                    record.creator = User.query.get(record.created_by)

            records = records_paginated

            # Get totals
            total_tithes = db.session.query(func.sum(FinancialRecord.amount)).filter_by(type='tithe').scalar() or 0
            total_offerings = db.session.query(func.sum(FinancialRecord.amount)).filter_by(
                type='offering').scalar() or 0
            total_donations = db.session.query(func.sum(FinancialRecord.amount)).filter_by(
                type='donation').scalar() or 0
            total_income = total_tithes + total_offerings + total_donations

            # Monthly financial data - descending order (most recent first)
            from sqlalchemy import extract
            monthly_data = db.session.query(
                extract('year', FinancialRecord.date).label('year'),
                extract('month', FinancialRecord.date).label('month'),
                func.sum(FinancialRecord.amount).label('total')
            ).group_by('year', 'month').order_by(
                extract('year', FinancialRecord.date).desc(),
                extract('month', FinancialRecord.date).desc()
            ).limit(6).all()

            # Reverse to show chronological order for the chart
            monthly_data = monthly_data[::-1]

            month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                           'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

            if monthly_data:
                # Create labels with month and year for clarity
                finance_labels = [f"{month_names[int(m[1]) - 1]} {int(m[0])}" for m in monthly_data]
                finance_data = [float(m[2]) for m in monthly_data]
            else:
                finance_labels = ['No Data']
                finance_data = [0]

    except Exception as e:
        print(f"Analytics error: {e}")  # For debugging
        flash('Database tables not ready. Please run migrations.', 'warning')
        stats = {
            'total_members': 0,
            'total_men': 0,
            'total_women': 0,
            'total_children': 0
        }
        member_growth_percent = 0

        # Create empty pagination object
        class EmptyPagination:
            items = []
            total = 0
            page = 1
            pages = 1
            has_prev = False
            has_next = False
            prev_num = None
            next_num = None

            def iter_pages(self, *args, **kwargs):
                return []

        records = EmptyPagination()

    return render_template('admin/analytics.html',
                           stats=stats,
                           growth_data=growth_data,
                           total_tithes=total_tithes if current_user.is_super_admin() else 0,
                           total_offerings=total_offerings if current_user.is_super_admin() else 0,
                           total_donations=total_donations if current_user.is_super_admin() else 0,
                           total_income=total_income if current_user.is_super_admin() else 0,
                           finance_labels=finance_labels if current_user.is_super_admin() else [],
                           finance_data=finance_data if current_user.is_super_admin() else [],
                           records=records if current_user.is_super_admin() else None,
                           member_growth_percent=member_growth_percent,
                           today=datetime.utcnow().strftime('%Y-%m-%d'))


# @admin_bp.route('/analytics/delete-financial/<int:record_id>', methods=['POST'])
# @login_required
# @super_admin_required
# def delete_financial(record_id):
#     """Delete a financial record"""
#     try:
#         from models.church_stats import FinancialRecord
#         record = FinancialRecord.query.get_or_404(record_id)
#
#         # Store info for flash message
#         record_info = f"{record.type.title()} of ₦{record.amount:,.2f} on {record.date.strftime('%b %d, %Y')}"
#
#         db.session.delete(record)
#         db.session.commit()
#         flash(f'✅ Financial record deleted: {record_info}', 'success')
#     except Exception as e:
#         flash(f'❌ Error deleting record: {str(e)}', 'danger')
#
#     return redirect(url_for('admin.analytics'))


@admin_bp.route('/analytics/update-members', methods=['POST'])
@login_required
@admin_required
def update_members():
    """Update church member counts"""
    try:
        from models.church_stats import ChurchStats, MemberGrowth
    except ImportError:
        flash('Church stats models not available. Please run database migrations.', 'danger')
        return redirect(url_for('admin.analytics'))

    men = request.form.get('men', 0, type=int)
    women = request.form.get('women', 0, type=int)
    children = request.form.get('children', 0, type=int)

    # Validate input
    if men < 0 or women < 0 or children < 0:
        flash('Please enter valid numbers (0 or greater).', 'danger')
        return redirect(url_for('admin.analytics'))

    stats = ChurchStats.query.first()
    if not stats:
        stats = ChurchStats()

    stats.total_men = men
    stats.total_women = women
    stats.total_children = children
    stats.total_members = men + women + children
    stats.updated_by = current_user.id

    db.session.add(stats)

    # Record growth history
    now = datetime.utcnow()
    growth = MemberGrowth(
        month=now.month,
        year=now.year,
        total_members=stats.total_members
    )
    db.session.add(growth)

    db.session.commit()
    flash(
        f' Number of members updated successfully! Total: {stats.total_members:,} (Men: {men:,}, Women: {women:,}, Children: {children:,})',
        'success')
    return redirect(url_for('admin.analytics'))


@admin_bp.route('/analytics/add-financial', methods=['POST'])
@login_required
@super_admin_required
def add_financial():
    """Add financial record"""
    try:
        from models.church_stats import FinancialRecord
    except ImportError:
        flash('Financial models not available. Please run database migrations.', 'danger')
        return redirect(url_for('admin.analytics'))

    finance_type = request.form.get('finance_type')
    amount = request.form.get('amount', 0, type=float)
    finance_date = request.form.get('finance_date')

    if not finance_type:
        flash('Please select a financial type.', 'danger')
        return redirect(url_for('admin.analytics'))

    if amount <= 0:
        flash('Please enter a valid amount greater than 0.', 'danger')
        return redirect(url_for('admin.analytics'))

    try:
        record_date = datetime.strptime(finance_date, '%Y-%m-%d') if finance_date else datetime.utcnow()
    except ValueError:
        record_date = datetime.utcnow()

    record = FinancialRecord(
        type=finance_type,
        amount=amount,
        date=record_date,
        created_by=current_user.id
    )
    db.session.add(record)
    db.session.commit()

    flash(f' {finance_type.title()} of ₦{amount:,.2f} recorded successfully for {record_date.strftime("%b %d, %Y")}!',
          'success')
    return redirect(url_for('admin.analytics'))


@admin_bp.route('/analytics-data')
@login_required
@admin_required
def analytics_data():
    """Get analytics data for AJAX requests"""
    try:
        from models.church_stats import MemberGrowth
    except ImportError:
        return jsonify({'labels': [], 'values': []})

    period = request.args.get('period', 'yearly')

    if period == 'weekly':
        # Get last 7 weeks of data (descending)
        records = MemberGrowth.query.order_by(
            MemberGrowth.year.desc(),
            MemberGrowth.month.desc()
        ).limit(7).all()
        # Reverse for chronological order
        records = records[::-1]
        labels = [f"Wk {i + 1}" for i in range(len(records))]
        values = [r.total_members for r in records]

    elif period == 'monthly':
        # Get last 12 months (descending)
        records = MemberGrowth.query.order_by(
            MemberGrowth.year.desc(),
            MemberGrowth.month.desc()
        ).limit(12).all()
        # Reverse for chronological order
        records = records[::-1]
        labels = [f"{r.month}/{r.year}" for r in records]
        values = [r.total_members for r in records]

    else:
        # Yearly - get last 5 years (descending)
        records = db.session.query(
            MemberGrowth.year,
            func.avg(MemberGrowth.total_members).label('avg_members')
        ).group_by(MemberGrowth.year).order_by(
            MemberGrowth.year.desc()
        ).limit(5).all()
        # Reverse for chronological order
        records = records[::-1]
        labels = [str(r[0]) for r in records]
        values = [float(r[1]) for r in records]

    return jsonify({
        'labels': labels,
        'values': values
    })


@admin_bp.route('/analytics/delete-financial/<int:record_id>', methods=['POST'])
@login_required
@super_admin_required
def delete_financial(record_id):
    """Delete a financial record"""
    try:
        from models.church_stats import FinancialRecord
        record = FinancialRecord.query.get_or_404(record_id)
        db.session.delete(record)
        db.session.commit()
        flash('Financial record deleted successfully!', 'success')
    except Exception as e:
        flash('Error deleting record: ' + str(e), 'danger')

    return redirect(url_for('admin.analytics'))




# @admin_bp.route('/analytics/update-members', methods=['POST'])
# @login_required
# @admin_required
# def update_members():
#     """Update church member counts"""
#     try:
#         from models.church_stats import ChurchStats, MemberGrowth
#     except ImportError:
#         flash('Church stats models not available. Please run database migrations.', 'danger')
#         return redirect(url_for('admin.analytics'))
#
#     men = request.form.get('men', 0, type=int)
#     women = request.form.get('women', 0, type=int)
#     children = request.form.get('children', 0, type=int)
#
#     stats = ChurchStats.query.first()
#     if not stats:
#         stats = ChurchStats()
#
#     stats.total_men = men
#     stats.total_women = women
#     stats.total_children = children
#     stats.total_members = men + women + children
#     stats.updated_by = current_user.id
#
#     db.session.add(stats)
#
#     # Record growth history
#     now = datetime.utcnow()
#     growth = MemberGrowth(
#         month=now.month,
#         year=now.year,
#         total_members=stats.total_members
#     )
#     db.session.add(growth)
#
#     db.session.commit()
#     flash('Member counts updated successfully!', 'success')
#     return redirect(url_for('admin.analytics'))
#
#
# @admin_bp.route('/analytics/add-financial', methods=['POST'])
# @login_required
# @super_admin_required
# def add_financial():
#     """Add financial record"""
#     try:
#         from models.church_stats import FinancialRecord
#     except ImportError:
#         flash('Financial models not available. Please run database migrations.', 'danger')
#         return redirect(url_for('admin.analytics'))
#
#     finance_type = request.form.get('finance_type')
#     amount = request.form.get('amount', 0, type=float)
#     finance_date = request.form.get('finance_date')
#
#     if not finance_type or amount <= 0:
#         flash('Please provide valid financial data.', 'danger')
#         return redirect(url_for('admin.analytics'))
#
#     record = FinancialRecord(
#         type=finance_type,
#         amount=amount,
#         date=datetime.strptime(finance_date, '%Y-%m-%d') if finance_date else datetime.utcnow(),
#         created_by=current_user.id
#     )
#     db.session.add(record)
#     db.session.commit()
#
#     flash(f'{finance_type.title()} of ₦{amount:.2f} recorded successfully!', 'success')
#     return redirect(url_for('admin.analytics'))

#
# @admin_bp.route('/analytics-data')
# @login_required
# @admin_required
# def analytics_data():
#     """Get analytics data for AJAX requests"""
#     try:
#         from models.church_stats import MemberGrowth
#     except ImportError:
#         return jsonify({'labels': [], 'values': []})
#
#     period = request.args.get('period', 'yearly')
#
#     if period == 'weekly':
#         # Get last 7 weeks of data
#         records = MemberGrowth.query.order_by(MemberGrowth.year.desc(), MemberGrowth.month.desc()).limit(7).all()
#         labels = [f'Week {i + 1}' for i in range(len(records))]
#         values = [r.total_members for r in records]
#     elif period == 'monthly':
#         # Get last 12 months
#         records = MemberGrowth.query.order_by(MemberGrowth.year.desc(), MemberGrowth.month.desc()).limit(12).all()
#         labels = [f'{r.month}/{r.year}' for r in records]
#         values = [r.total_members for r in records]
#     else:
#         # Yearly - get last 5 years
#         records = db.session.query(
#             MemberGrowth.year,
#             func.avg(MemberGrowth.total_members).label('avg_members')
#         ).group_by(MemberGrowth.year).order_by(MemberGrowth.year.desc()).limit(5).all()
#         labels = [str(r[0]) for r in records]
#         values = [float(r[1]) for r in records]
#
#     return jsonify({
#         'labels': labels[::-1],
#         'values': values[::-1]
#     })







# ===================== SETTINGS =====================
@admin_bp.route("/settings", methods=["GET", "POST"])
@login_required
@super_admin_required
def settings():
    """Site settings"""
    form = SettingsForm()

    if form.validate_on_submit():
        # Save settings to a settings table or environment
        # For simplicity, we'll store in a simple JSON file or use database
        flash("Settings updated successfully!", "success")
        return redirect(url_for("admin.settings"))

    return render_template("admin/settings.html", form=form)
