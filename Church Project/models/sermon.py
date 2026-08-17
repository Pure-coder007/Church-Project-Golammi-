from extensions import db
from datetime import datetime


class Sermon(db.Model):
    __tablename__ = "sermons"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    description = db.Column(db.Text)
    speaker = db.Column(db.String(100), nullable=False)
    category = db.Column(
        db.String(50), nullable=False, default="prophetic"
    )  # prophetic, teaching, worship, deliverance
    date_preached = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Media files
    audio_file = db.Column(db.String(255))  # Path to audio file
    video_url = db.Column(db.String(500))  # YouTube/Vimeo URL or custom URL
    live_stream_url = db.Column(
        db.String(500)
    )  # Facebook Live or other live stream URL
    thumbnail = db.Column(db.String(255))  # Thumbnail image path
    is_live = db.Column(db.Boolean, default=False)
    is_featured = db.Column(db.Boolean, default=False)
    is_published = db.Column(db.Boolean, default=True)

    # Download count
    download_count = db.Column(db.Integer, default=0)
    view_count = db.Column(db.Integer, default=0)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    updated_by = db.Column(db.Integer, db.ForeignKey("users.id"))

    def increment_download(self):
        self.download_count += 1
        db.session.commit()

    def increment_view(self):
        self.view_count += 1
        db.session.commit()

    def __repr__(self):
        return f"<Sermon {self.title}>"
