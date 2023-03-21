import os
from sqlalchemy import create_engine, event
import logging
import mimetypes

logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

engine = create_engine('sqlite:///repartidores.db')

@event.listens_for(engine, 'before_cursor_execute')
def log_query_info(conn, cursor, statement, parameters, context, executemany):
    logging.info(f'Query: {statement}; Parameters: {parameters}')

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'mysecretkey'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///repartidores.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    GOOGLE_MAPS_API_KEY = 'AIzaSyCZ9yapP5kLGP5zzuIeXaQX2iiT-W0JinA'

mimetypes.add_type('text/css', '.css')
mimetypes.add_type('application/javascript', '.js')
