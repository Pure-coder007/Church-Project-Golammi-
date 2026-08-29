from extensions import db
from datetime import datetime
from models.uuid_utils import uuid_pk_column, uuid_fk_column


class GalleryImage(db.Model):
    __tablename__ = "gallery_images"

    id = uuid_pk_column()
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(300))
    image_path = db.Column(db.String(255), nullable=False)
    thumbnail_path = db.Column(db.String(255))
    category = db.Column(
        db.String(50), nullable=False
    )  # worship, events, youth, outreach, prayer
    is_featured = db.Column(db.Boolean, default=False)
    is_published = db.Column(db.Boolean, default=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    created_by = uuid_fk_column("users.id")

    def __repr__(self):
        return f"<GalleryImage {self.title}>"
