from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo

class RegistrationForm(FlaskForm):
    username = StringField('Nombre de usuario', validators=[DataRequired()])
    email = StringField('Correo electrónico', validators=[DataRequired(), Email()])
    user_type = SelectField('Tipo de usuario', choices=[('usuario', 'Usuario'), ('repartidor', 'Repartidor')], validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    confirm_password = PasswordField('Confirmar contraseña', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Registrarse')

class LoginForm(FlaskForm):
    email = StringField('Correo electrónico', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    user_type = SelectField('Tipo de usuario', choices=[('usuario', 'Usuario'), ('repartidor', 'Repartidor')], validators=[DataRequired()])
    submit = SubmitField('Iniciar sesión')

class ActualizarEstadoForm(FlaskForm):
    status = SelectField('Estado', choices=[('pendiente', 'Pendiente'), ('en camino', 'En camino'), ('entregado', 'Entregado')], validators=[DataRequired()])
    submit = SubmitField('Actualizar')

