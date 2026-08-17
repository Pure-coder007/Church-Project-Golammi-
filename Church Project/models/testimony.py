from extensions import db
from datetime import datetime


class Testimony(db.Model):
    __tablename__ = 'testimonies'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_name = db.Column(db.String(100), nullable=False)
    author_email = db.Column(db.String(120))
    author_phone = db.Column(db.String(20))
    category = db.Column(db.String(50), nullable=False, default='healing')
    # categories: healing, deliverance, provision, family, salvation, other

    # Media
    image = db.Column(db.String(255))
    is_featured = db.Column(db.Boolean, default=False)
    is_approved = db.Column(db.Boolean, default=False)
    is_published = db.Column(db.Boolean, default=False)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    reviewed_at = db.Column(db.DateTime)

    # Relationship
    reviewer = db.relationship('User', foreign_keys=[reviewed_by])

    def __repr__(self):
        return f'<Testimony {self.title}>'