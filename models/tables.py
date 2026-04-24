from models import db
from flask_login import UserMixin
from datetime import datetime


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id          = db.Column(db.Integer, primary_key=True)
    username    = db.Column(db.String(64), unique=True, nullable=False)
    email       = db.Column(db.String(120), unique=True, nullable=False)
    password    = db.Column(db.String(256), nullable=False)
    avatar      = db.Column(db.String(256), default='default.png')
    age         = db.Column(db.Integer)
    gender      = db.Column(db.String(10))
    occupation  = db.Column(db.String(64))
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    is_active   = db.Column(db.Boolean, default=True)

    ratings     = db.relationship('Rating',   backref='user', lazy='dynamic')
    comments    = db.relationship('Comment',  backref='user', lazy='dynamic')
    favorites   = db.relationship('Favorite', backref='user', lazy='dynamic')


class Admin(UserMixin, db.Model):
    __tablename__ = 'admins'
    id          = db.Column(db.Integer, primary_key=True)
    username    = db.Column(db.String(64), unique=True, nullable=False)
    password    = db.Column(db.String(256), nullable=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)


class Movie(db.Model):
    __tablename__ = 'movies'
    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(256), nullable=False)
    genres      = db.Column(db.String(256))          # 用 | 分隔，如 Action|Comedy
    year        = db.Column(db.Integer)
    director    = db.Column(db.String(128))
    description = db.Column(db.Text)
    poster_url  = db.Column(db.String(512))
    avg_rating  = db.Column(db.Float, default=0.0)
    rating_count= db.Column(db.Integer, default=0)

    ratings     = db.relationship('Rating',   backref='movie', lazy='dynamic')
    comments    = db.relationship('Comment',  backref='movie', lazy='dynamic')
    favorites   = db.relationship('Favorite', backref='movie', lazy='dynamic')


class Rating(db.Model):
    __tablename__ = 'ratings'
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    movie_id    = db.Column(db.Integer, db.ForeignKey('movies.id'), nullable=False)
    rating      = db.Column(db.Float, nullable=False)   # 1.0 ~ 5.0
    timestamp   = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('user_id', 'movie_id'),)


class Comment(db.Model):
    __tablename__ = 'comments'
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    movie_id    = db.Column(db.Integer, db.ForeignKey('movies.id'), nullable=False)
    content     = db.Column(db.Text, nullable=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    is_visible  = db.Column(db.Boolean, default=True)


class Favorite(db.Model):
    __tablename__ = 'favorites'
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    movie_id    = db.Column(db.Integer, db.ForeignKey('movies.id'), nullable=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('user_id', 'movie_id'),)


class Log(db.Model):
    __tablename__ = 'logs'
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action      = db.Column(db.String(128))       # 如 login / view_movie / rate
    target_id   = db.Column(db.Integer)           # 操作对象 ID
    target_type = db.Column(db.String(32))        # movie / user / comment
    ip_address  = db.Column(db.String(64))
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)