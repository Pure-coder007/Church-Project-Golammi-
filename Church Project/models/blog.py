from extensions import db
from datetime import datetime
from models.uuid_utils import uuid_pk_column, uuid_fk_column


class BlogPost(db.Model):
    __tablename__ = "blog_posts"

    id = uuid_pk_column()
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    content = db.Column(db.Text, nullable=False)
    excerpt = db.Column(db.String(300))
    category = db.Column(
        db.String(50), nullable=False
    )  # Event, Ministry, Testimony, Youth, Prayer, Worship
    author = db.Column(db.String(100), nullable=False)

    # Media
    featured_image = db.Column(db.String(255))
    is_featured = db.Column(db.Boolean, default=False)
    is_published = db.Column(db.Boolean, default=True)

    # SEO
    meta_title = db.Column(db.String(200))
    meta_description = db.Column(db.String(300))
    meta_keywords = db.Column(db.String(300))

    # Timestamps
    published_date = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    created_by = uuid_fk_column("users.id")
    updated_by = uuid_fk_column("users.id")

    # Relationships
    comments = db.relationship(
        "BlogComment", backref="post", lazy=True, cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<BlogPost {self.title}>"


class BlogComment(db.Model):
    __tablename__ = "blog_comments"

    id = uuid_pk_column()
    post_id = uuid_fk_column("blog_posts.id", nullable=False)
    author_name = db.Column(db.String(100), nullable=False)
    author_email = db.Column(db.String(120))
    content = db.Column(db.Text, nullable=False)
    is_approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<BlogComment {self.author_name}>"
