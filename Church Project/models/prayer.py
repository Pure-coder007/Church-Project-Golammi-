from extensions import db
from datetime import datetime


class PrayerRequest(db.Model):
    __tablename__ = 'prayer_requests'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    category = db.Column(db.String(50), nullable=False)
    # categories: healing, deliverance, financial, family, career, salvation, general
    request = db.Column(db.Text, nullable=False)
    is_anonymous = db.Column(db.Boolean, default=False)
    is_prayed_for = db.Column(db.Boolean, default=False)
    is_answered = db.Column(db.Boolean, default=False)

    # Response
    response = db.Column(db.Text)
    responded_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    responded_at = db.Column(db.DateTime)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    responder = db.relationship('User', foreign_keys=[responded_by])

    def __repr__(self):
        return f'<PrayerRequest {self.full_name}>'