from datetime import datetime
from . import db

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

class LogEntry(db.Model):
    __tablename__ = 'logs'
    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(45), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    method = db.Column(db.String(10))
    url = db.Column(db.Text, nullable=False)
    protocol = db.Column(db.String(20))
    status = db.Column(db.Integer)
    size = db.Column(db.Integer)
    referer = db.Column(db.Text)
    user_agent = db.Column(db.Text)
    line_hash = db.Column(db.String(64), unique=True, index=True)

    def to_dict(self):
        return {
            'id': self.id,
            'ip': self.ip,
            'date': self.date.isoformat(),
            'method': self.method,
            'url': self.url,
            'protocol': self.protocol,
            'status': self.status,
            'size': self.size,
            'referer': self.referer,
            'user_agent': self.user_agent
        }
