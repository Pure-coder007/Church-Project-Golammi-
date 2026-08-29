import uuid

from extensions import db


def generate_uuid():
    return str(uuid.uuid4())


def uuid_pk_column():
    return db.Column(db.Uuid(as_uuid=False), primary_key=True, default=generate_uuid)


def uuid_fk_column(target, nullable=True):
    return db.Column(db.Uuid(as_uuid=False), db.ForeignKey(target), nullable=nullable)
