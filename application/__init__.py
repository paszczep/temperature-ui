from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from pathlib import Path
from dotenv import dotenv_values
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s: %(message)s'
)

parent_dir = Path(__file__).parent.parent
dotenv_dir = parent_dir / '.env'
dotenv_values = dotenv_values(dotenv_dir)

db = SQLAlchemy()
migrate = Migrate()


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = dotenv_values.get('SECRET_KEY')

    db_user = dotenv_values['DB_USER']
    db_password = dotenv_values['DB_PASSWORD']
    db_name = dotenv_values['DB_NAME']
    db_host = dotenv_values['DB_HOST']
    db_port = dotenv_values['DB_PORT']

    app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    migrate.init_app(app, db)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    from application.utility.models_application import AppUser

    @login_manager.user_loader
    def load_user(user_id):
        return AppUser.query.get(int(user_id))

    from application.views.auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from application.views.main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from application.views.control import control as control_blueprint
    app.register_blueprint(control_blueprint)

    from application.views.input_task import input_task as task_blueprint
    app.register_blueprint(task_blueprint)

    from application.views.input_set import input_set as set_blueprint
    app.register_blueprint(set_blueprint)

    return app


app = create_app()

