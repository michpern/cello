"""
This script runs the cello application using a development server.
"""

from os import environ
from cello import app, db, auth

if __name__ == '__main__':
    HOST = environ.get('SERVER_HOST', 'localhost')
    try:
        PORT = int(environ.get('SERVER_PORT', '5555'))
    except ValueError:
        PORT = 5555

    auth.User.create_table(fail_silently=True)
    app.run(HOST, PORT)
