# models.py

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate


db = SQLAlchemy()
migrate = Migrate()


class User(db.Model):
    __tablename__    = 'User'
    id               = db.Column(db.Integer, primary_key=True)
    line_id          = db.Column(db.String(255), nullable=False, unique=True)
    created_at       = db.Column(db.Float, nullable=False)
    coupon_issued    = db.Column(db.Boolean, nullable=False)
    name             = db.Column(db.String(255))
    email            = db.Column(db.String(255), unique=True)
    is_subscribing   = db.Column(db.Boolean)
    subscribed       = db.Column(db.Boolean)
    churned_at       = db.Column(db.Float)
    days_passed      = db.Column(db.Integer)
    default_time     = db.Column(db.String(255))
    num_of_referrals = db.Column(db.Integer)
    num_of_feedbacks = db.Column(db.Integer)
    enabled_weather  = db.Column(db.Boolean, nullable=False)
    enabled_twitter  = db.Column(db.Boolean, nullable=False)

    def __init__(self, line_id, created_at, coupon_issued=False, name=None, email=None, is_subscribing=None, subscribed=None, churned_at=None, days_passed=None, default_time=None, num_of_referrals=0, num_of_feedbacks=0, enabled_weather=True, enabled_twitter=False):
        self.line_id          = line_id
        self.created_at       = created_at
        self.coupon_issued    = coupon_issued
        self.name             = name
        self.email            = email
        self.is_subscribing   = is_subscribing
        self.subscribed       = subscribed
        self.churned_at       = churned_at
        self.days_passed      = days_passed
        self.default_time     = default_time
        self.num_of_referrals = num_of_referrals
        self.num_of_feedbacks = num_of_feedbacks
        self.enabled_weather  = enabled_weather
        self.enabled_twitter  = enabled_twitter
