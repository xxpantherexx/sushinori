from flask_migrate import Migrate, MigrateCommand
from my_project import app, db

migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)
