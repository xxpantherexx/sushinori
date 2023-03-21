from geopy.distance import geodesic

def calcular_tiempo_llegada(latitud_pedido, longitud_pedido, latitud_repartidor, longitud_repartidor, velocidad_entrega=40):
    # Creamos un objeto con la ubicación del pedido
    ubicacion_pedido = (latitud_pedido, longitud_pedido)
    # Creamos un objeto con la ubicación del repartidor
    ubicacion_repartidor = (latitud_repartidor, longitud_repartidor)
    # Calculamos la distancia entre los dos puntos
    distancia = geodesic(ubicacion_pedido, ubicacion_repartidor).km
    # Estimamos el tiempo de llegada asumiendo una velocidad promedio de entrega
    tiempo_llegada = distancia / velocidad_entrega
    # Retornamos el tiempo de llegada en horas
    return tiempo_llegada
