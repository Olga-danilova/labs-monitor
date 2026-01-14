import os
from flask import Flask
from flask_login import LoginManager
from database import db
from models import User

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'change_me_to_random_string'
    
    # Путь к БД: если есть папка /data (Amvera), то туда, иначе локально в instance
    if os.path.exists('/data'):
        db_path = '/data/journal.db'
    else:
        db_path = os.path.join(app.instance_path, 'journal.db')
        try:
            os.makedirs(app.instance_path)
        except OSError:
            pass
            
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    
    login_manager = LoginManager(app)
    login_manager.login_view = 'main.login' # <-- Важно: main.login

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, user_id)

    with app.app_context():
        db.create_all()
        # Создаем админа, если его нет
        if not db.session.get(User, 'admin')
            # Логин: admin, Пароль: admin
            admin = User(id='admin', password='admin', role='admin', access_group='all')
            db.session.add(admin)
            db.session.commit()

    # Регистрируем маршруты из routes.py
    from routes import main_bp
    app.register_blueprint(main_bp)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
