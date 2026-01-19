"""Скрипт для инициализации базы данных и создания админа."""
import os
from app import create_app
from database import db
from models import User
from werkzeug.security import generate_password_hash

def init_database():
    """Инициализирует базу данных и создает пользователя admin."""
    app = create_app()
    
    with app.app_context():
        # Создаем все таблицы
        db.create_all()
        print("Таблицы базы данных созданы")
        
        # Проверяем, есть ли уже админ
        admin = User.query.filter_by(role='admin').first()
        if admin:
            print(f"Администратор уже существует: {admin.id}")
        else:
            # Создаем нового админа
            admin = User(
                id='admin',
                password=generate_password_hash('admin123'),
                role='admin',
                access_group=None
            )
            db.session.add(admin)
            db.session.commit()
            print("Создан администратор:")
            print("  Логин: admin")
            print("  Пароль: admin123")

if __name__ == '__main__':
    init_database()
