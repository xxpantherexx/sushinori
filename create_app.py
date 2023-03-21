from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app(config_class):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)

    # Registrar blueprints aquí
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app
