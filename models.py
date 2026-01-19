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
    type = db.Column(db.String(50), default='Лекция')  # Лекция, Практика
        hours = db.Column(db.Integer, default=2)
    number = db.Column(db.Integer, nullable=True)  # Номер работы
    subgroup_target = db.Column(db.Integer, default=0)  # 0=все, 1/2=подгруппаtheа
    theme = db.Column(db.String(200), default='')
    
    # Связь с оценками
    grades = db.relationship('Grade', backref='lesson', lazy=True, cascade="all, delete-orphan")




class Grade(db.Model):
    id = db.Column(db.String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = db.Column(db.String(50), db.ForeignKey('student.id'), nullable=False)
    lesson_id = db.Column(db.String(50), db.ForeignKey('lesson.id'), nullable=False)
    status = db.Column(db.String(20), default='present')  # 'present', 'absent', 'sick'
    grade = db.Column(db.Integer, nullable=True)  # Оценка: 2, 3, 4, 5 или None


class Plan(db.Model):
    id = db.Column(db.String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    group_id = db.Column(db.String(50), db.ForeignKey('group.id'), nullable=False)
    semester = db.Column(db.Integer, nullable=False)  # 1 или 2
    data = db.Column(db.Text, default='[]')  # JSON с планом
    
    def get_data(self):
        try:
            return json.loads(self.data)
        except:
            return []
    
    def set_data(self, data_list):
        self.data = json.dumps(data_list, ensure_ascii=False)

class Announcement(db.Model):
    id = db.Column(db.String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    is_important = db.Column(db.Boolean, default=False)
    group_id = db.Column(db.String(50), db.ForeignKey('group.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
