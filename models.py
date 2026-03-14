from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), default='student')  # student or admin
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    profiles = db.relationship('StudentProfile', backref='user', uselist=False)
    assessments = db.relationship('SkillAssessment', backref='user')

class StudentProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    cgpa = db.Column(db.Float, nullable=False)
    branch = db.Column(db.String(50))
    skills = db.Column(db.Text)  # JSON or comma-separated
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SkillAssessment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    aptitude_score = db.Column(db.Integer, default=0)
    coding_score = db.Column(db.Integer, default=0)
    technical_score = db.Column(db.Integer, default=0)
    date_taken = db.Column(db.DateTime, default=datetime.utcnow)

# Admin can view all

