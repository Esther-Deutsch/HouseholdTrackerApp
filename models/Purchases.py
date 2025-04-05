from datetime import datetime
from extensions import db

class Purchases(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'),)
    name = db.Column(db.String)
    qty = db.Column(db.Integer, default = 1)
    price = db.Column(db.Numeric(precision=10,scale=2), nullable = False)
    category = db.Column(db.String)
    date = db.Column(db.DateTime, default = datetime.now())
    
