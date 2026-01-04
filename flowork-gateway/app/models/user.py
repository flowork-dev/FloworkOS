########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-gateway\app\models\user.py total lines 67 
########################################################################

from ..extensions import db
from datetime import datetime
import uuid

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    public_address = db.Column(db.String(42), unique=True, nullable=True)

    bio = db.Column(db.String(500), nullable=True)
    avatar = db.Column(db.String(255), nullable=True)

    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    engines = db.relationship('RegisteredEngine', backref='owner', lazy=True)
    subscriptions = db.relationship('Subscription', backref='user', lazy=True)
    engine_shares = db.relationship('EngineShare', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'

class RegisteredEngine(db.Model):
    __tablename__ = 'registered_engines'
    id = db.Column(db.String(36), primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    engine_token_hash = db.Column(db.String(256), nullable=False)
    status = db.Column(db.String(20), default='offline')
    last_seen = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Subscription(db.Model):
    __tablename__ = 'subscriptions'
    id = db.Column(db.String(36), primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    tier = db.Column(db.String(20), default='free')
    expires_at = db.Column(db.DateTime, nullable=True)

class EngineShare(db.Model):
    __tablename__ = 'engine_shares'
    id = db.Column(db.Integer, primary_key=True)
    engine_id = db.Column(db.String(36), db.ForeignKey('registered_engines.id'), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.String(20), default='reader')
    shared_at = db.Column(db.DateTime, default=datetime.utcnow)
    engine = db.relationship('RegisteredEngine', backref=db.backref('shares', cascade='all, delete-orphan'))

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)

class Permission(db.Model):
    __tablename__ = 'permissions'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)
