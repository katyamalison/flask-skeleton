# project/server/models.py


import datetime

from flask import current_app

from project.server import db, bcrypt

class Artist(db.Model):
    __tablename__ = 'artist'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name =  db.Column(db.String(255), unique=True, nullable=False)
    api_path = db.Column(db.String(255), unique=True, nullable=False)
    songs = db.relationship('Song')

    def __init__(self, name, api_path):
        self.name = name
        self.api_path = api_path
    
class Song(db.Model):
    __tablename__ = 'song'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(255), nullable=False)
    lyrics = db.Column(db.Text, nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'))

    def __init__(self, title, lyrics):
        self.title = title
        self.lyrics = lyrics

class User(db.Model):

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    registered_on = db.Column(db.DateTime, nullable=False)
    admin = db.Column(db.Boolean, nullable=False, default=False)

    def __init__(self, email, password, admin=False):
        self.email = email
        self.password = bcrypt.generate_password_hash(
            password, current_app.config.get('BCRYPT_LOG_ROUNDS')
        ).decode('utf-8')
        self.registered_on = datetime.datetime.now()
        self.admin = admin

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id

    def __repr__(self):
        return '<User {0}>'.format(self.email)
