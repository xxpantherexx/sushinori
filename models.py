from datetime import datetime
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from . import db

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    user_type = db.Column(db.String(32), nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)


class Repartidor(db.Model, UserMixin):
    __tablename__ = 'repartidor'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    user_type = db.Column(db.String(32), nullable=False, default='repartidor')
    latitud = db.Column(db.Float, nullable=True)
    longitud = db.Column(db.Float, nullable=True)
    ubi_lat_repartidor = db.Column(db.Float, nullable=True)  # Nueva columna
    ubi_long_repartidor = db.Column(db.Float, nullable=True)  # Nueva columna
    # ...resto de columnas

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = password
        self.is_active = True

    def check_password(self, password):
        return check_password_hash(self.password, password)


class Pedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    producto = db.Column(db.String(50))
    cantidad = db.Column(db.Integer)
    direccion_entrega = db.Column(db.String(120))
    usuario_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    repartidor_id = db.Column(db.Integer, db.ForeignKey('repartidor.id'))
    status = db.Column(db.String(20))
    latitud = db.Column(db.Float)
    longitud = db.Column(db.Float)

    usuario = db.relationship('User', backref=db.backref('pedidos', lazy=True))
    repartidor = db.relationship('Repartidor', backref=db.backref('pedidos', lazy=True))
    
class Mensaje(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    contenido = db.Column(db.Text, nullable=False)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedido.id'), nullable=False)
    enviado_por_cliente = db.Column(db.Boolean, nullable=False)
    fecha_hora = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __init__(self, contenido, pedido_id, enviado_por_cliente):
        self.contenido = contenido
        self.pedido_id = pedido_id
        self.enviado_por_cliente = enviado_por_cliente
    

