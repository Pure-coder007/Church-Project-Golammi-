from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import (
    StringField,
    TextAreaField,
    SelectField,
    BooleanField,
    DateTimeField,
    URLField,
    IntegerField,
    PasswordField,
    EmailField,
    HiddenField,
)
from wtforms.validators import DataRequired, Email, Length, Optional, URL, NumberRange


class LoginForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember Me")
    next = HiddenField()


class UserForm(FlaskForm):
    username = StringField(
        "Username", validators=[DataRequired(), Length(min=3, max=80)]
    )
    email = EmailField("Email", validators=[DataRequired(), Email()])
    full_name = StringField("Full Name", validators=[DataRequired(), Length(max=120)])
    role = SelectField(
        "Role",
        choices=[("admin", "Admin"), ("moderator", "Moderator"), ("editor", "Editor")],
    )
    password = PasswordField("Password", validators=[Optional(), Length(min=6)])
    is_active = BooleanField("Active")


class SermonForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=200)])
    description = TextAreaField("Description")
    speaker = StringField("Speaker", validators=[DataRequired(), Length(max=100)])
    category = SelectField(
        "Category",
        choices=[
            ("prophetic", "Prophetic"),
            ("teaching", "Teaching"),
            ("worship", "Worship"),
            ("deliverance", "Deliverance"),
        ],
        validators=[DataRequired()],
    )
    date_preached = DateTimeField("Date Preached", format="%Y-%m-%d %H:%M")
    audio_file = FileField(
        "Audio File",
        validators=[FileAllowed(["mp3", "wav", "ogg", "m4a"], "Audio files only")],
    )
    video_url = URLField("Video URL")
    live_stream_url = URLField("Live Stream URL")
    thumbnail = FileField(
        "Thumbnail Image",
        validators=[FileAllowed(["png", "jpg", "jpeg", "gif", "webp"], "Images only")],
    )
    is_live = BooleanField("Live Stream")
    is_featured = BooleanField("Featured")
    is_published = BooleanField("Published")


class EventForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=200)])
    description = TextAreaField("Description", validators=[DataRequired()])
    short_description = StringField("Short Description", validators=[Length(max=300)])
    category = SelectField(
        "Category",
        choices=[
            ("conference", "Conference"),
            ("worship", "Worship"),
            ("prayer", "Prayer"),
            ("deliverance", "Deliverance"),
            ("youth", "Youth"),
            ("outreach", "Outreach"),
        ],
        validators=[DataRequired()],
    )
    start_date = DateTimeField(
        "Start Date", format="%Y-%m-%d %H:%M", validators=[DataRequired()]
    )
    end_date = DateTimeField("End Date", format="%Y-%m-%d %H:%M")
    start_time = StringField("Start Time", validators=[Length(max=20)])
    end_time = StringField("End Time", validators=[Length(max=20)])
    location = StringField("Location", validators=[Length(max=200)])
    venue = StringField("Venue", validators=[Length(max=200)])
    is_online = BooleanField("Online Event")
    online_link = URLField("Online Link")
    image = FileField(
        "Event Image",
        validators=[FileAllowed(["png", "jpg", "jpeg", "gif", "webp"], "Images only")],
    )
    is_featured = BooleanField("Featured")
    is_published = BooleanField("Published")
    registration_required = BooleanField("Registration Required")
    registration_link = URLField("Registration Link")


class BlogForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=200)])
    content = TextAreaField("Content", validators=[DataRequired()])
    excerpt = StringField("Excerpt", validators=[Length(max=300)])
    category = SelectField(
        "Category",
        choices=[
            ("Event", "Event"),
            ("Ministry", "Ministry"),
            ("Testimony", "Testimony"),
            ("Youth", "Youth"),
            ("Prayer", "Prayer"),
            ("Worship", "Worship"),
        ],
        validators=[DataRequired()],
    )
    author = StringField("Author", validators=[DataRequired(), Length(max=100)])
    featured_image = FileField(
        "Featured Image",
        validators=[FileAllowed(["png", "jpg", "jpeg", "gif", "webp"], "Images only")],
    )
    is_featured = BooleanField("Featured")
    is_published = BooleanField("Published")
    meta_title = StringField("Meta Title", validators=[Length(max=200)])
    meta_description = StringField("Meta Description", validators=[Length(max=300)])
    meta_keywords = StringField("Meta Keywords", validators=[Length(max=300)])


class GalleryForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=200)])
    description = StringField("Description", validators=[Length(max=300)])
    category = SelectField(
        "Category",
        choices=[
            ("worship", "Worship"),
            ("events", "Events"),
            ("youth", "Youth"),
            ("outreach", "Outreach"),
            ("prayer", "Prayer"),
        ],
        validators=[DataRequired()],
    )
    image = FileField(
        "Image",
        validators=[
            FileRequired(),
            FileAllowed(["png", "jpg", "jpeg", "gif", "webp"], "Images only"),
        ],
    )
    is_featured = BooleanField("Featured")
    is_published = BooleanField("Published")


class RadioForm(FlaskForm):
    name = StringField("Station Name", validators=[DataRequired(), Length(max=100)])
    description = TextAreaField("Description")
    stream_url = URLField("Stream URL", validators=[DataRequired()])
    backup_url = URLField("Backup URL")
    is_active = BooleanField("Active")
    is_featured = BooleanField("Featured")
    cover_image = FileField(
        "Cover Image",
        validators=[FileAllowed(["png", "jpg", "jpeg", "gif", "webp"], "Images only")],
    )
    schedule = TextAreaField("Schedule")


class RadioScheduleForm(FlaskForm):
    day_of_week = SelectField(
        "Day of Week",
        choices=[
            (0, "Monday"),
            (1, "Tuesday"),
            (2, "Wednesday"),
            (3, "Thursday"),
            (4, "Friday"),
            (5, "Saturday"),
            (6, "Sunday"),
        ],
        validators=[DataRequired()],
    )
    start_time = StringField("Start Time", validators=[DataRequired(), Length(max=10)])
    end_time = StringField("End Time", validators=[DataRequired(), Length(max=10)])
    program_name = StringField(
        "Program Name", validators=[DataRequired(), Length(max=100)]
    )
    program_description = TextAreaField("Description")
    host = StringField("Host", validators=[Length(max=100)])


class TestimonyForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    content = TextAreaField('Content', validators=[DataRequired()])
    author_name = StringField('Author Name', validators=[DataRequired(), Length(max=100)])
    author_email = EmailField('Email', validators=[Optional(), Email()])
    author_phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    category = SelectField('Category', choices=[
        ('healing', 'Healing'),
        ('deliverance', 'Deliverance'),
        ('provision', 'Provision'),
        ('family', 'Family'),
        ('salvation', 'Salvation'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    image = FileField('Image', validators=[Optional(), FileAllowed(['png', 'jpg', 'jpeg', 'gif', 'webp'], 'Images only')])
    is_featured = BooleanField('Featured')
    is_approved = BooleanField('Approved')
    is_published = BooleanField('Published')


class PrayerRequestForm(FlaskForm):
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


class SettingsForm(FlaskForm):
    site_name = StringField("Site Name", validators=[DataRequired(), Length(max=100)])
    site_description = TextAreaField("Site Description", validators=[Length(max=500)])
    admin_email = EmailField("Admin Email", validators=[DataRequired(), Email()])
    facebook_url = URLField("Facebook URL")
    twitter_url = URLField("Twitter URL")
    instagram_url = URLField("Instagram URL")
    youtube_url = URLField("YouTube URL")
    whatsapp_url = URLField("WhatsApp URL")
    phone = StringField("Phone", validators=[Length(max=20)])
    address = TextAreaField("Address", validators=[Length(max=300)])
    footer_text = TextAreaField("Footer Text", validators=[Length(max=500)])
