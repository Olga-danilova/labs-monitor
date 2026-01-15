import uuid
import json
from flask_login import UserMixin
from database import db
from datetime import datetime


class User(UserMixin, db.Model):
    id = db.Column(db.String(50), primary_key=True)
    password = db.Column(db.String(100))
    role = db.Column(db.String(20))  # 'admin', 'teacher', 'student'
    access_group = db.Column(db.String(50), nullable=True)  # для учителя/студента


class Group(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    subject = db.Column(db.String(100), default='Предмет')
    
    # Связь со студентами
    students = db.relationship('Student', backref='group', lazy=True, cascade="all, delete-orphan")
    # Связь с занятиями
    lessons = db.relationship('Lesson', backref='group', lazy=True, cascade="all, delete-orphan")
    # Связь с планами
    plans = db.relationship('Plan', backref='group', lazy=True, cascade="all, delete-orphan")
    # Связь с объявлениями
    announcements = db.relationship('Announcement', backref='group', lazy=True, cascade="all, delete-orphan")


class Student(db.Model):
    id = db.Column(db.String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    subgroup = db.Column(db.Integer, default=1)  # 1 или 2
    group_id = db.Column(db.String(50), db.ForeignKey('group.id'), nullable=False)
    
    # Связь с оценками
    grades = db.relationship('Grade', backref='student', lazy=True, cascade="all, delete-orphan")


class Lesson(db.Model):
    id = db.Column(db.String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    date = db.Column(db.Date, nullable=False)
    lesson_type = db.Column(db.String(50), default='Лекция')  # Лекция, Практика
    theme = db.Column(db.String(200), default='')
    subgroup = db.Column(db.Integer, nullable=True)  # null = общее, 1/2 = подгруппа
    group_id = db.Column(db.String(50), db.ForeignKey('group.id'), nullable=False)
    
    # Связь с оценками
    grades = db.relationship('Grade', backref='lesson', lazy=True, cascade="all, delete-orphan")


class Grade(db.Model):
    id = db.Column(db.String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = db.Column(db.String(50), db.ForeignKey('student.id'), nullable=False)
    lesson_id = db.Column(db.String(50), db.ForeignKey('lesson.id'), nullable=False)
    attendance = db.Column(db.String(20), default='Не отмечен')  # Присутствовал, Отсутствовал, Не отмечен
    lab_statuses = db.Column(db.Text, default='{}')  # JSON: {"1": "Сдано", "2": "Не сдано", ...}
    notes = db.Column(db.Text, default='')  # Примечания
    
    def get_lab_statuses(self):
        try:
            return json.loads(self.lab_statuses)
        except:
            return {}
    
    def set_lab_statuses(self, data):
        self.lab_statuses = json.dumps(data, ensure_ascii=False)


class Plan(db.Model):
    id = db.Column(db.String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default='')
    group_id = db.Column(db.String(50), db.ForeignKey('group.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Announcement(db.Model):
    id = db.Column(db.String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    group_id = db.Column(db.String(50), db.ForeignKey('group.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
