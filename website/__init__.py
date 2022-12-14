from flask import Flask
from flask.json import jsonify
# from website.constants.http_status_codes import HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager
from flask_marshmallow import Marshmallow
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
db = SQLAlchemy()
DB_NAME = "database.db"
app = Flask(__name__)
jwt = JWTManager(app)
ma = Marshmallow(app)
mail = Mail(app)

def create_app():
    app.config['SECRET_KEY'] = "helloWorld"
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    app.config['MAIL_SERVER'] = 'smtp.mailtrap.io'
    app.config['MAIL_PORT'] = 2525
    app.config['MAIL_USERNAME'] = 'c63ebe40617db8'
    app.config['MAIL_PASSWORD'] = '742899a32b8120'
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USE_SSL'] = False
    db.init_app(app)
    from .auth import auth
    from .views import views

    app.register_blueprint(auth, url_prefix="/")
    app.register_blueprint(views, url_prefix="/")

    from .models import User, Resere, Room
    create_database(app)

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    # @app.errorhandler(HTTP_404_NOT_FOUND)
    # def handle_404(e):
    #     return jsonify({'error': 'Not found'}), HTTP_404_NOT_FOUND
    #
    # @app.errorhandler(HTTP_500_INTERNAL_SERVER_ERROR)
    # def handle_500(e):
    #     return jsonify({'error': 'Something went wrong, we are working on it'}), HTTP_500_INTERNAL_SERVER_ERROR
    #

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app


def create_database(app):
    if not path.exists("website/" + DB_NAME):
        db.create_all(app=app)
        print("Created database!")
