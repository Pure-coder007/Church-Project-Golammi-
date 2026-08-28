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
from models.contact import ContactMessage
from models.prayer import PrayerRequest
from models.donation import DonationSubmission
from forms import PrayerRequestForm, TestimonyForm
from extensions import db
from datetime import datetime
from sqlalchemy import case
import re

frontend_bp = Blueprint("frontend", __name__)

DEFAULT_PAYMENT_ACCOUNTS = [
    {
        "bank_name": "WEMA BANK",
        "account_name": "GOLAMMI WORSHIP CENTRE",
        "account_number": "0123923413",
    },
]


def get_payment_accounts():
    accounts = current_app.config.get("CHURCH_PAYMENT_ACCOUNTS")
    return accounts if accounts else DEFAULT_PAYMENT_ACCOUNTS


def has_letters(value):
    return any(char.isalpha() for char in (value or ""))


def is_valid_reason(reason):
    return reason in {"prayer", "testimony", "giving", "general"}


def get_event_modal_event():
    now = datetime.utcnow()
    featured_upcoming = (
        Event.query.filter(
            Event.is_published == True,
            Event.image.isnot(None),
            Event.image != "",
            db.or_(Event.end_date.is_(None), Event.end_date >= now),
            Event.is_featured == True,
        )
        .order_by(Event.start_date.asc(), Event.created_at.desc())
        .first()
    )
    if featured_upcoming:
        return featured_upcoming

    upcoming = (
        Event.query.filter(
            Event.is_published == True,
            Event.image.isnot(None),
            Event.image != "",
            db.or_(Event.end_date.is_(None), Event.end_date >= now),
        )
        .order_by(Event.start_date.asc(), Event.created_at.desc())
        .first()
    )
    if upcoming:
        return upcoming

    return (
        Event.query.filter(
            Event.is_published == True,
            Event.image.isnot(None),
            Event.image != "",
        )
        .order_by(Event.created_at.desc())
        .first()
    )


@frontend_bp.app_context_processor
def inject_frontend_event_modal():
    show_event_modal = request.endpoint == "frontend.index"
    return {
        "event_modal_event": get_event_modal_event() if show_event_modal else None,
    }


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
    live_sermon = (
        Sermon.query.filter(
            Sermon.is_published == True,
            Sermon.is_live == True,
            Sermon.live_stream_url.isnot(None),
            Sermon.live_stream_url != "",
        )
        .order_by(Sermon.date_preached.desc(), Sermon.created_at.desc())
        .first()
    )
    testimonies = (
        Testimony.query.filter_by(is_published=True, is_approved=True)
        .order_by(Testimony.created_at.desc())
        .limit(3)
        .all()
    )

    return render_template(
        "frontend/index.html",
        featured_sermons=featured_sermons,
        upcoming_events=upcoming_events,
        latest_blog=latest_blog,
        recent_sermons=recent_sermons,
        live_sermon=live_sermon,
        testimonies=testimonies,
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

    now = datetime.utcnow()
    query = Event.query.filter(Event.is_published == True)

    if category != "all":
        query = query.filter_by(category=category)

    future_first = case((Event.start_date >= now, 0), else_=1)

    events = query.order_by(future_first, Event.start_date.asc()).paginate(
        page=page, per_page=current_app.config["EVENTS_PER_PAGE"], error_out=False
    )

    featured_event = (
        Event.query.filter_by(is_featured=True, is_published=True)
        .order_by(future_first, Event.start_date.asc())
        .first()
    )

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
    now = datetime.utcnow()
    related_events = (
        Event.query.filter(
            Event.id != event.id,
            Event.is_published == True,
            Event.category == event.category,
        )
        .order_by(
            case((Event.start_date >= now, 0), else_=1),
            Event.start_date.asc(),
        )
        .limit(3)
        .all()
    )
    return render_template(
        "frontend/event_detail.html",
        event=event,
        related_events=related_events,
        now=now,
    )


@frontend_bp.route('/prayer', methods=['GET', 'POST'])
def prayer():
    """Prayer page"""
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
        flash('Your prayer request has been submitted. Our prayer team will pray for you.', 'success')
        return redirect(url_for('frontend.prayer'))

    return render_template('frontend/prayer.html', form=form)


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


@frontend_bp.route("/giving", methods=["GET", "POST"])
def giving():
    """Giving page"""
    form_data = {
        "name": "",
        "email": "",
        "phone": "",
        "giving_type": "",
        "amount": "",
        "message": "",
        "anonymous": False,
    }
    payment_accounts = get_payment_accounts()
    show_payment_modal = False
    payment_submission = None

    if request.method == "POST":
        form_data = {
            "name": (request.form.get("name") or "").strip(),
            "email": (request.form.get("email") or "").strip(),
            "phone": (request.form.get("phone") or "").strip(),
            "giving_type": (request.form.get("giving_type") or "").strip(),
            "amount": (request.form.get("amount") or "").strip(),
            "message": (request.form.get("message") or "").strip(),
            "anonymous": request.form.get("anonymous") == "on",
        }
        errors = []

        if not form_data["name"]:
            errors.append("Full name is required.")
        elif not has_letters(form_data["name"]):
            errors.append("Full name must contain letters.")
        if not form_data["email"]:
            errors.append("Email address is required.")
        elif not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", form_data["email"]):
            errors.append("Enter a valid email address.")
        if form_data["phone"] and re.search(r"[A-Za-z]", form_data["phone"]):
            errors.append("Phone number must not contain letters.")
        if not form_data["giving_type"]:
            errors.append("Please select a giving type.")

        try:
            amount = float(form_data["amount"])
            if amount <= 0:
                raise ValueError
        except ValueError:
            errors.append("Enter a valid amount greater than 0.")
            amount = None

        if errors:
            for error in errors:
                flash(error, "danger")
        else:
            donation = DonationSubmission(
                full_name=form_data["name"],
                email=form_data["email"],
                phone=form_data["phone"] or None,
                giving_type=form_data["giving_type"],
                amount=amount,
                message=form_data["message"] or None,
                is_anonymous=form_data["anonymous"],
            )
            db.session.add(donation)
            db.session.commit()

            payment_submission = donation
            show_payment_modal = True
            flash(
                "Your giving details have been received. Use any of the account numbers below to complete your payment.",
                "success",
            )
            form_data = {
                "name": "",
                "email": "",
                "phone": "",
                "giving_type": "",
                "amount": "",
                "message": "",
                "anonymous": False,
            }

    return render_template(
        "frontend/giving.html",
        payment_accounts=payment_accounts,
        show_payment_modal=show_payment_modal,
        payment_submission=payment_submission,
        form_data=form_data,
    )


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


@frontend_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact page"""
    if request.method == 'POST':
        name = (request.form.get('name') or '').strip()
        email = (request.form.get('email') or '').strip()
        phone = (request.form.get('phone') or '').strip()
        reason = (request.form.get('reason') or '').strip()
        subject = (request.form.get('subject') or '').strip()
        message = (request.form.get('message') or '').strip()

        if not name or not email or not subject or not message:
            flash('Please fill in all required fields.', 'danger')
            return redirect(url_for('frontend.contact'))

        if not has_letters(name):
            flash('Full name must contain letters.', 'danger')
            return redirect(url_for('frontend.contact'))

        if phone and re.search(r"[A-Za-z]", phone):
            flash('Phone number must not contain letters.', 'danger')
            return redirect(url_for('frontend.contact'))

        if not is_valid_reason(reason):
            flash('Please choose a valid reason for contacting us.', 'danger')
            return redirect(url_for('frontend.contact'))

        if reason in {'prayer', 'testimony'} and not has_letters(subject):
            flash('Subject must contain letters.', 'danger')
            return redirect(url_for('frontend.contact'))

        if reason == 'testimony':
            testimony = Testimony(
                title=subject,
                content=message,
                author_name=name,
                author_email=email,
                author_phone=phone or None,
                category='other',
                image=None,
                is_featured=False,
                is_approved=False,
                is_published=False,
            )
            db.session.add(testimony)
        elif reason == 'prayer':
            prayer_request = PrayerRequest(
                full_name=name,
                email=email,
                phone=phone or None,
                category='general',
                request=message,
                is_anonymous=False,
            )
            db.session.add(prayer_request)
        else:
            contact_msg = ContactMessage(
                name=name,
                email=email,
                phone=phone or None,
                reason=reason,
                subject=subject,
                message=message
            )
            db.session.add(contact_msg)

        db.session.commit()

        if reason == 'testimony':
            flash('Your testimony has been received and is now pending admin review before publication.', 'success')
        elif reason == 'prayer':
            flash('Your prayer request has been received and sent to the prayer team.', 'success')
        else:
            flash('Your message has been sent successfully! Our team will get back to you within 24-48 hours.', 'success')
        return redirect(url_for('frontend.contact'))

    return render_template('frontend/contact.html')


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
