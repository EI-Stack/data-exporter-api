from data_exporter import db
from datetime import datetime


def isodatetime():
    dt = datetime.utcnow()
    microsecond = int(dt.microsecond / 1000) * 1000
    dt = dt.replace(microsecond=microsecond)
    return dt


class Waconn(db.Document):
    uuid = db.UUIDField(required=True, unique=True)
    type = db.StringField()
    status = db.IntField()
    ts = db.DateTimeField()
    created_at = db.DateTimeField(default=isodatetime)


class Wadata(db.Document):
    uuid = db.UUIDField(required=True, unique=True)
    tag_id = db.StringField()
    value = db.FloatField()
    ts = db.DateTimeField()
    created_at = db.DateTimeField(default=isodatetime)


class Wacfg(db.Document):
    uuid = db.UUIDField(required=True, unique=True)
    tag_status = db.StringField()
    tag_id = db.StringField()
    device_type = db.StringField()
    ts = db.DateTimeField()
    created_at = db.DateTimeField(default=isodatetime)


class SpcData(db.Document):
    uuid = db.UUIDField(required=True, unique=True)
    ParameterID = db.StringField()
    value_list = db.StringField()
    created_at = db.DateTimeField(default=isodatetime)
