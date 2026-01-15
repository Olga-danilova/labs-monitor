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
    
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице.'
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Регистрируем blueprints
    # Регистрируем blueprints
    from routes import main_bp    
    
    app.register_blueprint(main_bp)    
    # Создаём таблицы при первом запуске
    with app.app_context():
        db.create_all()
        # Создаём администратора по умолчанию
        from utils import create_default_admin
        create_default_admin()
    
    return app


if __name__ == '__main__':
    app = create_app()
    port = int(os.getenv('PORT') or 8000)
    app.run(debug=True, host='0.0.0.0', port=port)
