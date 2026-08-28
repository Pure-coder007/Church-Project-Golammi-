from datetime import datetime

from extensions import db


class ActivityLog(db.Model):
    __tablename__ = "activity_logs"

    id = db.Column(db.Integer, primary_key=True)
    occurred_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    method = db.Column(db.String(10), nullable=False)
    path = db.Column(db.String(500), nullable=False)
    endpoint = db.Column(db.String(200))
    section = db.Column(db.String(50), nullable=False, default="frontend")
    action_label = db.Column(db.String(255), nullable=False)
    request_summary = db.Column(db.String(255), nullable=False)
    status_code = db.Column(db.Integer, nullable=False)
    response_time_ms = db.Column(db.Integer, nullable=False, default=0)
    ip_address = db.Column(db.String(64))
    visitor_key = db.Column(db.String(64))
    user_agent = db.Column(db.String(500))
    referrer = db.Column(db.String(500))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    user = db.relationship("User", foreign_keys=[user_id])

    def __repr__(self):
        return f"<ActivityLog {self.method} {self.path} {self.status_code}>"
