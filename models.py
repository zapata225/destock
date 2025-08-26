from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    full_name = db.Column(db.String(200))
    address = db.Column(db.String(200))
    phone = db.Column(db.String(50))
    role = db.Column(db.String(20), default="user")  # "user" ou "admin"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    payment_methods = db.relationship('PaymentMethod', backref='user', lazy=True)
    orders = db.relationship('Order', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class PaymentMethod(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    card_number = db.Column(db.String(20), nullable=False)
    expiry = db.Column(db.String(10), nullable=False)
    card_name = db.Column(db.String(100))
    cvv = db.Column(db.String(5))
    default = db.Column(db.Boolean, default=False)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class Order(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    reference = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(50))
    delivery_address = db.Column(db.String(250))
    billing_address = db.Column(db.String(250))
    date = db.Column(db.DateTime, default=datetime.utcnow)
    subtotal = db.Column(db.Float, default=0.0)
    delivery_method = db.Column(db.String(50), default='standard')
    delivery_cost = db.Column(db.Float, default=0.0)
    discount = db.Column(db.Float, default=0.0)
    total = db.Column(db.Float, default=0.0)
    promo_code = db.Column(db.String(50))
    payment_method = db.Column(db.String(50))
    status = db.Column(db.String(50), default='En traitement')
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    items = db.Column(db.JSON)  # Stocke le panier sous forme de JSON
