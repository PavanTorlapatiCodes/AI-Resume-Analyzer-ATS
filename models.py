from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)
    resumes = db.relationship('Resume', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class Resume(db.Model):
    __tablename__ = 'resumes'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    filename = db.Column(db.String(256), nullable=False)
    original_name = db.Column(db.String(256), nullable=False)
    job_title = db.Column(db.String(256))
    job_description = db.Column(db.Text)
    ats_score = db.Column(db.Float, default=0.0)
    keyword_score = db.Column(db.Float, default=0.0)
    format_score = db.Column(db.Float, default=0.0)
    skills_score = db.Column(db.Float, default=0.0)
    matched_keywords = db.Column(db.Text)   # JSON string
    missing_keywords = db.Column(db.Text)   # JSON string
    extracted_skills = db.Column(db.Text)   # JSON string
    recommendations = db.Column(db.Text)    # JSON string
    word_count = db.Column(db.Integer, default=0)
    sections_found = db.Column(db.Text)     # JSON string
    report_path = db.Column(db.String(256))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    analyzed_at = db.Column(db.DateTime)

    def __repr__(self):
        return f'<Resume {self.original_name}>'
