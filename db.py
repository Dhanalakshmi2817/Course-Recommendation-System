from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate

# Initialize Flask application
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SECRET_KEY'] = 'your_secret_key'

# Initialize database and migration tools
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    favorites = db.relationship('Favorite', back_populates='user')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
class Favorite(db.Model):
    __tablename__ = 'favorite'
 
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    role = db.Column(db.String, nullable=False)
    courses = db.Column(db.String, nullable=False)
    skills = db.Column(db.String, nullable=False)
    salary = db.Column(db.Float, nullable=False)

    user = db.relationship('User', back_populates='favorites')
# Entry point to create database and tables
if __name__ == '__main__':
    with app.app_context():  # Create application context
       # db.drop_all()  # WARNING: This will drop all tables; be careful when running this!
        db.create_all()  # Create the database and tables
        print("Database created!")
