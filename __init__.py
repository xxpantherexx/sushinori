from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///repartidores.db'
    app.config['SECRET_KEY'] = 'mysecretkey'
    db.init_app(app)
    
    from my_project.routes import main_routes
    app.register_blueprint(main_routes)

    return app
