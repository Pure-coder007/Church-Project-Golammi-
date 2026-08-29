from extensions import db
from datetime import datetime
from models.uuid_utils import uuid_pk_column, uuid_fk_column


class RadioStation(db.Model):
    __tablename__ = "radio_stations"

    id = uuid_pk_column()
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    stream_url = db.Column(db.String(500), nullable=False)  # Audio stream URL
    backup_url = db.Column(db.String(500))  # Backup stream URL
    is_active = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)
    cover_image = db.Column(db.String(255))

    # Schedule
    schedule = db.Column(db.Text)  # JSON or plain text schedule

    # Currently playing
    current_track = db.Column(db.String(200))
    current_artist = db.Column(db.String(100))
    current_album = db.Column(db.String(200))

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    created_by = uuid_fk_column("users.id")

    def __repr__(self):
        return f"<RadioStation {self.name}>"


class RadioSchedule(db.Model):
    __tablename__ = "radio_schedules"

    id = uuid_pk_column()
    station_id = uuid_fk_column("radio_stations.id", nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)  # 0-6 (Monday-Sunday)
    start_time = db.Column(db.String(10), nullable=False)  # HH:MM format
    end_time = db.Column(db.String(10), nullable=False)
    program_name = db.Column(db.String(100), nullable=False)
    program_description = db.Column(db.Text)
    host = db.Column(db.String(100))

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    created_by = uuid_fk_column("users.id")

    def __repr__(self):
        return f"<RadioSchedule {self.program_name}>"
