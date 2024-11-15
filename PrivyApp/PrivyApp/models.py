from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from passlib.hash import pbkdf2_sha256
import base64

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

    def set_password(self, password):
        self.password_hash = pbkdf2_sha256.hash(password)

    def check_password(self, password):
        return pbkdf2_sha256.verify(password, self.password_hash)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    reason = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # = db.relationship('User', backref=db.backref('personal', lazy=True))

class Password(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    #user = db.relationship('User', backref=db.backref('personal', lazy=True))

    service_name = db.Column(db.String(500), nullable=False)
    username = db.Column(db.String(200), nullable=False)
    password_encrypted = db.Column(db.String(255), nullable=False)

    def set_password(self, password):
        self.password_encrypted = self.encode_string(password)

    def get_password(self):
        return self.decode_string(self.password_encrypted)

    def encode_string(self,input_string):
        # Convert the string to bytes
        input_bytes = input_string.encode('utf-8')
        # Encode the bytes using base64
        encoded_bytes = base64.b64encode(input_bytes)
        # Convert the encoded bytes back to a string
        encoded_string = encoded_bytes.decode('utf-8')
        return encoded_string

    def decode_string(self,encoded_string):
        # Convert the encoded string to bytes
        encoded_bytes = encoded_string.encode('utf-8')
        # Decode the bytes using base64
        decoded_bytes = base64.b64decode(encoded_bytes)
        # Convert the decoded bytes back to a string
        decoded_string = decoded_bytes.decode('utf-8')
        return decoded_string
