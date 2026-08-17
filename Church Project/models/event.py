from extensions import db
from datetime import datetime


class Event(db.Model):
    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    short_description = db.Column(db.String(300))
    category = db.Column(
        db.String(50), nullable=False, default="conference"
    )  # worship, prayer, deliverance, conference, youth

    # Date and time
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime)
    start_time = db.Column(db.String(20))
    end_time = db.Column(db.String(20))

    # Location
    location = db.Column(db.String(200))
    venue = db.Column(db.String(200))
    is_online = db.Column(db.Boolean, default=False)
    online_link = db.Column(db.String(500))

    # Media
    image = db.Column(db.String(255))
    is_featured = db.Column(db.Boolean, default=False)
    is_published = db.Column(db.Boolean, default=True)

    # Registration
    registration_required = db.Column(db.Boolean, default=False)
    registration_link = db.Column(db.String(500))

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    updated_by = db.Column(db.Integer, db.ForeignKey("users.id"))

    def __repr__(self):
        return f"<Event {self.title}>"
