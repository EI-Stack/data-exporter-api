import logging

from apscheduler.schedulers.blocking import BlockingScheduler
from flask import Flask
from flask_apscheduler import APScheduler

from .config import config
from flask_mqtt import Mqtt
from flask_mongoengine import MongoEngine

mqtt = Mqtt()
db = MongoEngine()
scheduler = APScheduler()
# socketio = SocketIO()


def create_app(config_name="development"):
    app = Flask(__name__)
    with app.app_context():
        app.config.from_object(config[config_name])
        config[config_name].init_app(app)
        # socketio.init_app(app)

        # models.init_app(app)
        mqtt.init_app(app)
        db.init_app(app)
        from . import routes
        LOGGING_FORMAT = '%(asctime)s %(levelname)s: %(message)s'
        DATE_FORMAT = '[%Y-%m-%d %H:%M:%S]'
        logging.basicConfig(level=logging.INFO, format=LOGGING_FORMAT, datefmt=DATE_FORMAT)
        routes.init_app(app)
        scheduler.init_app(app)
        scheduler.start()

    return app
