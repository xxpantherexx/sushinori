from flask import Flask, render_template, redirect, url_for, flash, request
from flask_migrate import Migrate
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from .models import db, User, Repartidor, Pedido, Mensaje
from my_project.forms import RegistrationForm, LoginForm, ActualizarEstadoForm
from flask_googlemaps import GoogleMaps
from flask_googlemaps import Map
from geopy.distance import distance
from geopy.distance import geodesic
from .utils import calcular_tiempo_llegada
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from .config import Config

# Importamos la biblioteca requests para hacer solicitudes HTTP a la API de Google Maps
import requests
import json

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")
app.config['SECRET_KEY'] = 'mysecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///repartidores.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config.from_object(Config)

db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

@app.route('/')
def home():
    print(app.config['GOOGLE_MAPS_API_KEY'])
    return render_template('home.html')

@app.route('/cliente/pedido/<int:pedido_id>')
def cliente_pedido(pedido_id):
    # Obtenemos el pedido correspondiente a pedido_id
    pedido = Pedido.query.get(pedido_id)

    # Obtenemos la dirección del pedido
    direccion = pedido.direccion

    # Hacemos una solicitud HTTP a la API de Google Maps para obtener las coordenadas de latitud y longitud de la dirección
    response = requests.get(f'https://maps.googleapis.com/maps/api/geocode/json?address={direccion}&key={app.config["GOOGLE_MAPS_API_KEY"]}')
    data = response.json()
    latitud = data['results'][0]['geometry']['location']['lat']
    longitud = data['results'][0]['geometry']['location']['lng']

    # Pasamos las coordenadas de latitud y longitud a la vista pedido.html
    return render_template('cliente/pedido.html', pedido=pedido, latitud=latitud, longitud=longitud)
    
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        user_type = form.user_type.data

        if user_type == 'repartidor':
            repartidor = Repartidor(username=username, email=email, password=generate_password_hash(password))
            db.session.add(repartidor)
        else:  # cliente
           user = User(username=username, email=email)
           user.set_password(password)
           user.type = 'cliente'
           db.session.add(user)

        db.session.commit()
        flash('Registro completado exitosamente. Por favor, inicia sesión.')
        return redirect(url_for('login'))

    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user_type = form.user_type.data
        if user_type == 'repartidor':
            user = Repartidor.query.filter_by(email=email).first()
        else:
            user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Inicio de sesión exitoso.')
            return redirect(url_for('dashboard'))
        else:
            flash('Correo electrónico o contraseña incorrectos. Por favor, inténtalo de nuevo.')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada exitosamente.')
    return redirect(url_for('home'))
    
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')
    
@login_manager.user_loader
def load_user(user_id):
    if user_id.isdigit():
        user = User.query.get(int(user_id))
        if user:
            return user
        else:
            return Repartidor.query.get(int(user_id))
    else:
        return Repartidor.query.get(user_id)
   
@app.route('/ubicacion_repartidor')
def ubicacion_repartidor():
    # Obtenemos la ubicación del repartidor (aquí asumimos que es fija, pero podrías usar una API de geolocalización para obtenerla en tiempo real)
    ubicacion_repartidor = {
        'lat': 37.7749,
        'lng': -122.4194
    }
    # Calculamos el tiempo estimado de entrega (aquí asumimos que es de 30 minutos)
    tiempo_estimado = datetime.now() + timedelta(minutes=30)
    # Devolvemos la respuesta al cliente en formato JSON
    respuesta = {
        'ubicacion_repartidor': ubicacion_repartidor,
        'tiempo_estimado': tiempo_estimado.strftime('%Y-%m-%d %H:%M:%S')
    }
    return jsonify(respuesta)
    
@app.route('/pedido/<int:id>')
def pedido(id):
    pedido = Pedido.query.get(id)
    repartidor = pedido.repartidor

    # obtener la ubicación del repartidor y la dirección de entrega del pedido
    latitud_repartidor = repartidor.ubi_lat_repartidor
    longitud_repartidor = repartidor.ubi_long_repartidor
    latitud_pedido = pedido.latitud
    longitud_pedido = pedido.longitud

    # calcular el tiempo de llegada
    api_key = ''
    origen = (latitud_repartidor, longitud_repartidor)
    destino = (latitud_pedido, longitud_pedido)
    coordenadas, tiempo_llegada = obtener_ruta_y_tiempo(origen, destino, api_key)

    # obtener los mensajes relacionados con el pedido
    mensajes = Mensaje.query.filter_by(pedido_id=id).order_by(Mensaje.fecha_hora).all()

    return render_template('pedido.html', pedido=pedido, tiempo_llegada=tiempo_llegada, mensajes=mensajes, google_maps_api_key='')

def obtener_ruta_y_tiempo(origen, destino, api_key):
    base_url = "https://maps.googleapis.com/maps/api/directions/json?"
    parametros = f"origin={origen[0]},{origen[1]}&destination={destino[0]},{destino[1]}&key={api_key}"
    url = base_url + parametros

    response = requests.get(url)
    data = json.loads(response.text)

    if data['status'] == 'OK':
        ruta = data['routes'][0]['overview_polyline']['points']
        tiempo = data['routes'][0]['legs'][0]['duration']['text']
        return ruta, tiempo
    else:
        return None, None
        
@socketio.on('enviar_mensaje')
def handle_send_message(data):
    contenido = data['contenido']
    pedido_id = data['pedido_id']
    enviado_por_cliente = data['enviado_por_cliente']

    # Guardar el mensaje en la base de datos
    mensaje = Mensaje(contenido=contenido, pedido_id=pedido_id, enviado_por_cliente=enviado_por_cliente)
    db.session.add(mensaje)
    db.session.commit()

    # Emitir el mensaje a los clientes y repartidores
    emit('recibir_mensaje', data, broadcast=True)

# Lista de clientes conectados
connected_clients = []


# Función para manejar la conexión de nuevos clientes
@socketio.on('connect')
def handle_connect():
    # Agregar el ID del cliente a la lista de clientes conectados
    connected_clients.append(request.sid)
    # Enviar la lista de clientes conectados a todos los clientes
    emit('connected_clients', connected_clients, broadcast=True)

# Función para manejar la desconexión de clientes
@socketio.on('disconnect')
def handle_disconnect():
    # Remover el ID del cliente de la lista de clientes conectados
    connected_clients.remove(request.sid)
    # Enviar la lista de clientes conectados a todos los clientes
    emit('connected_clients', connected_clients, broadcast=True)
           
@app.route('/localizar_pedido', methods=['GET', 'POST'])
def localizar_pedido():
    if request.method == 'POST':
        pedido_id = request.form['pedido_id']
        pedido = Pedido.query.get(pedido_id)
        if not pedido:
            flash('Pedido no encontrado', 'error')
            return redirect(url_for('localizar_pedido'))
        repartidor = Repartidor.query.get(pedido.repartidor_id)
        ubicacion_actual = repartidor.obtener_ubicacion_actual()
        tiempo_estimado = calcular_tiempo_estimado(pedido.direccion_entrega, ubicacion_actual)
        return render_template('pedido.html', pedido=pedido, repartidor=repartidor, ubicacion_actual=ubicacion_actual, tiempo_estimado=tiempo_estimado)
    return render_template('localizar_pedido.html')

@app.route('/pedido/<int:pedido_id>/ubicacion')
@login_required
def ubicacion_pedido(pedido_id):
    # Busca el pedido por su ID
    pedido = Pedido.query.get_or_404(pedido_id)
    
    # Obtiene la dirección de entrega del pedido
    direccion_entrega = pedido.direccion_entrega
    
    # Obtiene el repartidor asignado al pedido
    repartidor = Repartidor.query.get(pedido.repartidor_id)
    
    # Obtiene la ubicación actual del repartidor
    ubicacion_actual = repartidor.obtener_ubicacion_actual()
    
    # Calcula el tiempo estimado de entrega
    tiempo_estimado = calcular_tiempo_estimado(direccion_entrega, ubicacion_actual)
    
    # Renderiza la plantilla con la información del pedido y la ubicación en un mapa
    return render_template('ubicacion_pedido.html', pedido=pedido, direccion_entrega=direccion_entrega, ubicacion_repartidor=ubicacion_actual, tiempo_estimado=tiempo_estimado, api_key=app.config['GOOGLE_MAPS_API_KEY'])

@app.route('/crear_pedido', methods=['GET', 'POST'])
def crear_pedido():
    # Obtiene un usuario de la base de datos (puede ser cualquiera)
    usuario = User.query.first()

    # Obtiene un repartidor de la base de datos (puede ser cualquiera)
    repartidor = Repartidor.query.first()

    # Maneja el caso en el que no se encuentren registros de usuario o repartidor
    if not usuario:
        flash('No se encontraron usuarios en la base de datos.', 'error')
        return redirect(url_for('home'))
    if not repartidor:
        flash('No se encontraron repartidores en la base de datos.', 'error')
        return redirect(url_for('home'))

    # Crea un nuevo pedido y lo guarda en la base de datos
    pedido = Pedido(producto='Producto de prueba', cantidad=1, direccion_entrega='123 Calle Falsa', usuario_id=usuario.id, repartidor_id=repartidor.id)
    db.session.add(pedido)
    db.session.commit()

    flash('Pedido creado exitosamente.', 'success')
    return redirect(url_for('home'))
   
@app.route('/pedidos_usuario/<string:username>')
def pedidos_usuario(username):
    usuario = User.query.filter_by(username=username).first()
    if usuario:
        pedidos = usuario.pedidos
        return render_template('pedidos_usuario.html', usuario=usuario, pedidos=pedidos)
    else:
        flash('Usuario no encontrado', 'error')
        return redirect(url_for('home'))
        
@app.route('/buscar_pedido', methods=['GET', 'POST'])
def buscar_pedido():
    if request.method == 'POST':
        pedido_id = request.form['id']
        pedido = Pedido.query.get(pedido_id)
        if not pedido:
            flash('Pedido no encontrado', 'error')
            return redirect(url_for('buscar_pedido'))
        return redirect(url_for('pedido', id=pedido.id))  # cambiar 'pedido_id' por 'id'
    return render_template('buscar_pedido.html')
    
@app.route('/pedido/<int:pedido_id>')
def mostrar_pedido(pedido_id):
    # Busca el pedido por su ID
    pedido = Pedido.query.get_or_404(pedido_id)
    
    # Obtiene el repartidor asignado al pedido
    repartidor = Repartidor.query.get(pedido.repartidor_id)
    
    # Obtiene la ubicación actual del repartidor
    ubicacion_actual = repartidor.obtener_ubicacion_actual()
    
    # Calcula el tiempo estimado de entrega
    tiempo_estimado = calcular_tiempo_estimado(pedido.direccion_entrega, ubicacion_actual)
    
    # Renderiza la plantilla con la información del pedido y la ubicación en un mapa
    return render_template('pedido.html', pedido=pedido, google_maps_api_key=app.config['GOOGLE_MAPS_API_KEY'])
    
@app.route("/map")
def map():
    # Define the map's center coordinates
    center = {'lat': 37.7749, 'lng': -122.4194}

    # Create the map object with the center coordinates
    mymap = Map(
        identifier="view-side",
        lat=center['lat'],
        lng=center['lng'],
        markers=[(center['lat'], center['lng'])],
        style="height:500px;width:100%;",
        zoom=12,
        apikey=app.config['GOOGLE_MAPS_API_KEY']
    )

    # Render the map template with the map object
    return render_template('map.html', mymap=mymap)
   
@app.route('/actualizar_estado/<int:id>', methods=['GET', 'POST'])
@login_required
def actualizar_estado(id):
    pedido = Pedido.query.get_or_404(id)

    if current_user.user_type != 'repartidor':
        abort(403)

    form = ActualizarEstadoForm()

    if form.validate_on_submit():
        try:
            print(f'Se está actualizando el estado del pedido {id} a {form.status.data}')
            pedido.status = form.status.data
            db.session.commit()
            flash('El estado del pedido ha sido actualizado.')
            return redirect(url_for('ver_pedido', id=id))
        except Exception as e:
            print('Error actualizando pedido:', e)
            db.session.rollback()
            flash('Ha ocurrido un error al actualizar el estado del pedido.', 'error')
    else:
        print(f'El formulario no se ha enviado. Errores: {form.errors}')

    return render_template('pedido.html', pedido=pedido, form=form, google_maps_api_key=app.config['GOOGLE_MAPS_API_KEY'])


@app.route('/editar_pedido/<int:id>', methods=['GET'])
def editar_pedido(id):
    # Buscamos el pedido a editar
    pedido = Pedido.query.get(id)
    # Renderizamos la plantilla con el formulario para editar el pedido
    return render_template('editar_pedido.html', pedido=pedido)
  
@app.route('/repartidores/<int:id>/pedidos')
@login_required
def lista_pedidos_repartidor(id):
    repartidor = Repartidor.query.get_or_404(id)
    pedidos = Pedido.query.filter_by(repartidor_id=id).all()
    return render_template('lista_pedidos_repartidor.html', repartidor=repartidor, pedidos=pedidos)
    
@app.route('/pedidos/<int:id>', methods=['GET'])
@login_required
def ver_pedido(id):
    pedido = Pedido.query.get_or_404(id)

    # Obtenemos la ruta y el tiempo estimado de llegada
    api_key = 'TU_CLAVE_API_DE_GOOGLE_MAPS'
    origen = 'La dirección del repartidor'
    destino = pedido.direccion_entrega
    coordenadas, tiempo = obtener_ruta_y_tiempo(origen, destino, api_key)

    return render_template('ver_pedido.html', pedido=pedido, coordenadas=coordenadas, tiempo=tiempo)

@app.route('/pedidos/<int:id>/modificar_estado', methods=['POST'])
@login_required
def modificar_estado_pedido(id):
    pedido = Pedido.query.get_or_404(id)
    estado = request.form.get('estado')

    if estado:
        pedido.estado = estado
        db.session.commit()

    return redirect(url_for('lista_pedidos_repartidor', id=pedido.repartidor_id))
       
if __name__ == '__main__':
    socketio.run(app, debug=True)


