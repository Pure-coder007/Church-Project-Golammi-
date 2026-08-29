from extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from models.uuid_utils import uuid_pk_column


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = uuid_pk_column()
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    role = db.Column(
        db.String(50), nullable=False, default="admin"
    )  # super_admin, admin, moderator, editor
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    last_login = db.Column(db.DateTime)

    # Relationships
    created_sermons = db.relationship(
        "Sermon", backref="creator", lazy=True, foreign_keys="Sermon.created_by"
    )
    updated_sermons = db.relationship(
        "Sermon", backref="updater", lazy=True, foreign_keys="Sermon.updated_by"
    )
    created_events = db.relationship(
        "Event", backref="creator", lazy=True, foreign_keys="Event.created_by"
    )
    updated_events = db.relationship(
        "Event", backref="updater", lazy=True, foreign_keys="Event.updated_by"
    )
    created_blog_posts = db.relationship(
        "BlogPost", backref="creator", lazy=True, foreign_keys="BlogPost.created_by"
    )
    updated_blog_posts = db.relationship(
        "BlogPost", backref="updater", lazy=True, foreign_keys="BlogPost.updated_by"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_role(self, role):
        if self.role == "super_admin":
            return True
        return self.role == role

    def is_super_admin(self):
        return self.role == "super_admin"

    def is_admin(self):
        return self.role in ["super_admin", "admin"]

    def is_moderator(self):
        return self.role in ["super_admin", "admin", "moderator"]

    def __repr__(self):
        return f"<User {self.username}>"
