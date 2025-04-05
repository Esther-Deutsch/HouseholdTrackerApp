from extensions import db
from flask_login import UserMixin

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable = False)
    email = db.Column(db.String, unique=True, nullable = False)
    password = db.Column(db.String, nullable = False)

    