# -*- coding: utf-8 -*-
# __init__.py

import os
from flask import Flask


config = {
    'development': 'config.Development',
    'testing': 'config.Testing',
    'production': 'config.Production'
}


# Application Factory
def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config[os.getenv('FLASK_MODE', 'production')])

    from .models import db, migrate
    db.init_app(app)
    migrate.init_app(app, db)

    return app
