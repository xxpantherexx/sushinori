from my_project import create_app
from my_project.models import Repartidor

app = create_app()
app.app_context().push()

repartidor = Repartidor(username='repartidor1', email='repartidor1@example.com', password='password')
db.session.add(repartidor)
db.session.commit()

print("Repartidor creado exitosamente")
