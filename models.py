from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    full_name = db.Column(db.String(200))
    address = db.Column(db.String(200))
    phone = db.Column(db.String(50))
    role = db.Column(db.String(20), default="user")  # "user" ou "admin"

    # Relation vers les cartes
    payment_methods = db.relationship('PaymentMethod', backref='user', lazy=True)

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
