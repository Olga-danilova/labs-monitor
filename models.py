import uuid
import json
from flask_login import UserMixin
from database import db
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.String(50), primary_key=True)
    password = db.Column(db.String(100))
    role = db.Column(db.String(20))
    access_group = db.Column(db.String(50), nullable=True)

class Group(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    subject = db.Column(db.String(100), default='Предмет')
    
    students = db.relationship('Student', backref='group', lazy=True, cascade="all, delete-orphan")
    lessons = db.relationship('Lesson', backref='group', lazy=True, cascade="all, delete-orphan")
    plans = db.relationship('Plan', backref='group', lazy=True, cascade="all, delete-orphan")
    announcements = db.relationship('Announcement', backref='group', lazy=True, cascade="all, delete-orphan")

class Student(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    subgroup = db.Column(db.Integer, default=1)
    group_id = db.Column(db.String(50), db.ForeignKey('group.id'), nullable=False)
    marks = db.relationship('Mark', backref='student', lazy=True, cascade="all, delete-orphan")

class Lesson(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    date = db.Column(db.String(20), nullable=False)
    type = db.Column(db.String(50))
    number = db.Column(db.Integer, nullable=True)
    subgroup_target = db.Column(db.Integer, default=0)
    is_continued = db.Column(db.Boolean, default=False)
    hours = db.Column(db.Integer, default=2)
    semester = db.Column(db.Integer, default=1)
    group_id = db.Column(db.String(50), db.ForeignKey('group.id'), nullable=False)
    marks = db.relationship('Mark', backref='lesson', lazy=True, cascade="all, delete-orphan")

class Mark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(36), db.ForeignKey('student.id'), nullable=False)
    lesson_id = db.Column(db.String(36), db.ForeignKey('lesson.id'), nullable=False)
    grade = db.Column(db.Integer, nullable=True)
    
    # НОВОЕ ПОЛЕ ДЛЯ СТАРОЙ ОЦЕНКИ
    old_grade = db.Column(db.Integer, nullable=True)
    
    status = db.Column(db.String(20), default='present')
    __table_args__ = (db.UniqueConstraint('student_id', 'lesson_id', name='_student_lesson_uc'),)

class Plan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.String(50), db.ForeignKey('group.id'), nullable=False)
    semester = db.Column(db.Integer, default=1)
    data = db.Column(db.Text, default='[]')
    __table_args__ = (db.UniqueConstraint('group_id', 'semester', name='_group_semester_plan_uc'),)

    def get_data(self):
        try: return json.loads(self.data)
        except: return []

    def set_data(self, data_list):
        self.data = json.dumps(data_list, ensure_ascii=False)

class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.String(50), db.ForeignKey('group.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    is_important = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
