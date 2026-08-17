from flask import (
    Blueprint,
    render_template,
    request,
    flash,
    redirect,
    url_for,
    current_app,
)
from models.sermon import Sermon
from models.event import Event
from models.blog import BlogPost
from models.gallery import GalleryImage
from models.radio import RadioStation
from models.testimony import Testimony
from models.prayer import PrayerRequest
from forms import PrayerRequestForm, TestimonyForm
from extensions import db
from datetime import datetime

frontend_bp = Blueprint("frontend", __name__)


@frontend_bp.route("/")
def index():
    """Home page"""
    featured_sermons = (
        Sermon.query.filter_by(is_featured=True, is_published=True).limit(3).all()
    )
    upcoming_events = (
        Event.query.filter(
            Event.start_date >= datetime.utcnow(), Event.is_published == True
        )
        .order_by(Event.start_date)
        .limit(3)
        .all()
    )
    latest_blog = (
        BlogPost.query.filter_by(is_published=True)
        .order_by(BlogPost.created_at.desc())
        .limit(3)
        .all()
    )
    recent_sermons = (
        Sermon.query.filter_by(is_published=True)
        .order_by(Sermon.created_at.desc())
        .limit(6)
        .all()
    )

    return render_template(
        "frontend/index.html",
        featured_sermons=featured_sermons,
        upcoming_events=upcoming_events,
        latest_blog=latest_blog,
        recent_sermons=recent_sermons,
    )


@frontend_bp.route("/about")
def about():
    """About page"""
    return render_template("frontend/about.html")


@frontend_bp.route("/sermons")
def sermons():
    """Sermons page"""
    page = request.args.get("page", 1, type=int)
    category = request.args.get("category", "all")
    search = request.args.get("search", "")

    query = Sermon.query.filter_by(is_published=True)

    if category != "all":
        query = query.filter_by(category=category)

    if search:
        query = query.filter(
            db.or_(
                Sermon.title.contains(search),
                Sermon.speaker.contains(search),
                Sermon.description.contains(search),
            )
        )

    sermons = query.order_by(Sermon.date_preached.desc()).paginate(
        page=page, per_page=current_app.config["SERMONS_PER_PAGE"], error_out=False
    )

    featured_sermon = Sermon.query.filter_by(
        is_featured=True, is_published=True
    ).first()

    return render_template(
        "frontend/sermons.html",
        sermons=sermons,
        featured_sermon=featured_sermon,
        category=category,
        search=search,
    )


@frontend_bp.route("/sermons/<slug>")
def sermon_detail(slug):
    """Sermon detail page"""
    sermon = Sermon.query.filter_by(slug=slug, is_published=True).first_or_404()
    sermon.increment_view()

    related_sermons = (
        Sermon.query.filter(
            Sermon.id != sermon.id,
            Sermon.is_published == True,
            Sermon.category == sermon.category,
        )
        .limit(3)
        .all()
    )

    return render_template(
        "frontend/sermon_detail.html", sermon=sermon, related_sermons=related_sermons
    )


@frontend_bp.route("/events")
def events():
    """Events page"""
    page = request.args.get("page", 1, type=int)
    category = request.args.get("category", "all")

    query = Event.query.filter(
        Event.start_date >= datetime.utcnow(), Event.is_published == True
    )

    if category != "all":
        query = query.filter_by(category=category)

    events = query.order_by(Event.start_date).paginate(
        page=page, per_page=current_app.config["EVENTS_PER_PAGE"], error_out=False
    )

    featured_event = Event.query.filter_by(is_featured=True, is_published=True).first()

    return render_template(
        "frontend/events.html",
        events=events,
        featured_event=featured_event,
        category=category,
    )


@frontend_bp.route("/events/<slug>")
def event_detail(slug):
    """Event detail page"""
    event = Event.query.filter_by(slug=slug, is_published=True).first_or_404()
    return render_template("frontend/event_detail.html", event=event)


@frontend_bp.route("/prayer", methods=["GET", "POST"])
def prayer():
    """Prayer page"""
    form = PrayerRequestForm()

    if form.validate_on_submit():
        prayer = PrayerRequest(
            full_name=(
                form.full_name.data if not form.is_anonymous.data else "Anonymous"
            ),
            email=form.email.data,
            phone=form.phone.data,
            category=form.category.data,
            request=form.request.data,
            is_anonymous=form.is_anonymous.data,
        )
        db.session.add(prayer)
        db.session.commit()
        flash(
            "Your prayer request has been submitted. Our prayer team will pray for you.",
            "success",
        )
        return redirect(url_for("frontend.prayer"))

    return render_template("frontend/prayer.html", form=form)


@frontend_bp.route("/media")
def media():
    """Media page"""
    page = request.args.get("page", 1, type=int)
    category = request.args.get("category", "all")

    query = Sermon.query.filter_by(is_published=True)

    if category != "all":
        query = query.filter_by(category=category)

    media_items = query.order_by(Sermon.created_at.desc()).paginate(
        page=page, per_page=6, error_out=False
    )

    return render_template(
        "frontend/media.html", media_items=media_items, category=category
    )


@frontend_bp.route("/giving")
def giving():
    """Giving page"""
    return render_template("frontend/giving.html")


@frontend_bp.route("/blog")
def blog():
    """Blog page"""
    page = request.args.get("page", 1, type=int)
    category = request.args.get("category", "all")
    search = request.args.get("search", "")

    query = BlogPost.query.filter_by(is_published=True)

    if category != "all":
        query = query.filter_by(category=category)

    if search:
        query = query.filter(
            db.or_(
                BlogPost.title.contains(search),
                BlogPost.content.contains(search),
                BlogPost.excerpt.contains(search),
            )
        )

    posts = query.order_by(BlogPost.published_date.desc()).paginate(
        page=page, per_page=current_app.config["POSTS_PER_PAGE"], error_out=False
    )

    categories = (
        db.session.query(BlogPost.category, db.func.count(BlogPost.id))
        .filter_by(is_published=True)
        .group_by(BlogPost.category)
        .all()
    )
    recent_posts = (
        BlogPost.query.filter_by(is_published=True)
        .order_by(BlogPost.created_at.desc())
        .limit(5)
        .all()
    )

    return render_template(
        "frontend/blog.html",
        posts=posts,
        categories=categories,
        recent_posts=recent_posts,
        category=category,
        search=search,
    )


@frontend_bp.route("/blog/<slug>")
def blog_detail(slug):
    """Blog detail page"""
    post = BlogPost.query.filter_by(slug=slug, is_published=True).first_or_404()
    recent_posts = (
        BlogPost.query.filter(BlogPost.id != post.id, BlogPost.is_published == True)
        .order_by(BlogPost.created_at.desc())
        .limit(5)
        .all()
    )

    return render_template(
        "frontend/blog_detail.html", post=post, recent_posts=recent_posts
    )


@frontend_bp.route("/gallery")
def gallery():
    """Gallery page"""
    page = request.args.get("page", 1, type=int)
    category = request.args.get("category", "all")

    query = GalleryImage.query.filter_by(is_published=True)

    if category != "all":
        query = query.filter_by(category=category)

    images = query.order_by(GalleryImage.created_at.desc()).paginate(
        page=page, per_page=12, error_out=False
    )

    return render_template("frontend/gallery.html", images=images, category=category)


@frontend_bp.route("/radio")
def radio():
    """Radio page"""
    station = RadioStation.query.filter_by(is_active=True).first()
    schedules = None

    if station:
        # Get schedules for today (or all)
        pass

    return render_template("frontend/radio.html", station=station, schedules=schedules)


@frontend_bp.route("/faq")
def faq():
    """FAQ page"""
    return render_template("frontend/faq.html")


@frontend_bp.route("/contact", methods=["GET", "POST"])
def contact():
    """Contact page"""
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        subject = request.form.get("subject")
        message = request.form.get("message")

        # Send email or save to database
        flash("Your message has been sent. We will get back to you soon.", "success")
        return redirect(url_for("frontend.contact"))

    return render_template("frontend/contact.html")


@frontend_bp.route("/privacy")
def privacy():
    """Privacy policy page"""
    return render_template("frontend/privacy.html")


@frontend_bp.route("/terms-of-service")
def terms():
    """Terms of service page"""
    return render_template("frontend/terms-of-service.html")


@frontend_bp.route("/school-of-prophets", methods=["GET", "POST"])
def school_of_prophets():
    """School of Prophets page"""
    if request.method == "POST":
        # Handle registration form submission
        flash(
            "Registration submitted successfully! We will contact you soon.", "success"
        )
        return redirect(url_for("frontend.school_of_prophets"))

    return render_template("frontend/school-of-prophets.html")
