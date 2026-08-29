from extensions import db
from datetime import datetime
from models.uuid_utils import uuid_pk_column, uuid_fk_column


# models/contact.py

class ContactMessage(db.Model):
    __tablename__ = 'contact_messages'

    id = uuid_pk_column()
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    reason = db.Column(db.String(50), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    is_replied = db.Column(db.Boolean, default=False)
    replied_at = db.Column(db.DateTime)
    replied_by = uuid_fk_column('users.id')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    replier = db.relationship('User', foreign_keys=[replied_by])

    def __repr__(self):
        return f'<ContactMessage {self.name} - {self.subject}>'
