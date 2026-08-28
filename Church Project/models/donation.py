from datetime import datetime

from extensions import db


class DonationSubmission(db.Model):
    __tablename__ = "donation_submissions"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    giving_type = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    message = db.Column(db.Text)
    is_anonymous = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<DonationSubmission {self.full_name} - {self.giving_type}>"
