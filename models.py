# models.py

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate


db = SQLAlchemy()
migrate = Migrate()


class User(db.Model):
    __tablename__ = 'User'
    id       = db.Column(db.Integer, primary_key=True)
    line_id  = db.Column(db.String(255), nullable=False, unique=True)
    name     = db.Column(db.String(255))
    gender   = db.Column(db.String(255))
    email    = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    payment  = db.Column(db.Integer)
    address  = db.Column(db.String(255))

    def __init__(self, line_id, name=None, gender=None, email=None, password=None, payment=None, address=None):
        self.line_id  = line_id
        self.name     = name
        self.gender   = gender
        self.email    = email
        self.password = password
        self.payment  = payment
        self.address  = address
