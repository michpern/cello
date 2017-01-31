"""
The flask application package.
"""

from flask import Flask
app = Flask(__name__)

# flask-peewee bindings
from flask_peewee.db import Database
from flask_peewee.auth import Auth
from flask_peewee.admin import Admin

# configure our database
DATABASE = {
    'name': 'tracker.db',
    'engine': 'peewee.SqliteDatabase',
}
#DEBUG = True
SECRET_KEY = 'ssshhhh'

app = Flask(__name__)
app.config.from_object(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

# instantiate the db wrapper
db = Database(app)

auth = Auth(app, db)

admin = Admin(app, auth)
#admin.register(Note)

admin.setup()
import cello.views
