#-*- coding: utf-8 -*-

import os
from pg import DB
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
#from flask_debugtoolbar import DebugToolbarExtension
from flask_mail import Mail, Message
# from views import db_connection

#from .db_connection import getDB
# db = db_connection.getDB()

def create_app(test_config=None):

    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.debug=True
    formatter = logging.Formatter(
        "[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s")
    handler = RotatingFileHandler('/var/log/project/arctic.log', maxBytes=10000000, backupCount=5)
    handler.setFormatter(formatter)
    #handler = RotatingFileHandler('/var/log/project/arctic.log', maxBytes=10000, backupCount=1)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)

    mail = Mail(app)
    from views import app_config as cfg

    app.config.from_mapping(
        SECRET_KEY=cfg.app_secret_key,
        #DATABASE=os.path.join(app.instance_path, 'taskapp.sqlite'),
        DEBUG_TB_INTERCEPT_REDIRECTS=False,
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        SERVER_NAME='178.128.189.120',
        SESSION_COOKIE_PATH='/home'
    )
    mail = Mail(app)
    # toolbar=DebugToolbarExtension(app)
    logging.basicConfig(filename='/var/log/project/twinn.log', format='%(asctime)s %(message)s',level=logging.INFO)



    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass



    from views import auth
    app.register_blueprint(auth.bp)
    from views import register
    app.register_blueprint(register.bp)
    from views import dashboard
    app.register_blueprint(dashboard.bp)
    app.add_url_rule('/home',endpoint='index')
    app.add_url_rule('/',endpoint='index2')
    # app.add_url_rule('/',endpoint='index')
    from views import users
    app.register_blueprint(users.bp)
    from views import task
    app.register_blueprint(task.bp)
    from views import settings
    app.register_blueprint(settings.bp)

    return app

app=create_app()
