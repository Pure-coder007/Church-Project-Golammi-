from extensions import db
from datetime import datetime


class ChurchStats(db.Model):
    __tablename__ = 'church_stats'

    id = db.Column(db.Integer, primary_key=True)
    total_members = db.Column(db.Integer, default=0)
    total_men = db.Column(db.Integer, default=0)
    total_women = db.Column(db.Integer, default=0)
    total_children = db.Column(db.Integer, default=0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __repr__(self):
        return f'<ChurchStats Members: {self.total_members}>'


class FinancialRecord(db.Model):
    __tablename__ = 'financial_records'

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)  # tithe, offering, donation
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    description = db.Column(db.String(200))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<FinancialRecord {self.type}: ${self.amount}>'


class MemberGrowth(db.Model):
    __tablename__ = 'member_growth'

    id = db.Column(db.Integer, primary_key=True)
    month = db.Column(db.Integer, nullable=False)  # 1-12
    year = db.Column(db.Integer, nullable=False)
    total_members = db.Column(db.Integer, nullable=False)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<MemberGrowth {self.month}/{self.year}: {self.total_members}>'