from flask import Flask
from .config import config
from flask_mqtt import Mqtt
from flask_mongoengine import MongoEngine

mqtt = Mqtt()
db = MongoEngine()
# socketio = SocketIO()
def create_app(config_name='development'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    # socketio.init_app(app)

    # models.init_app(app)
    mqtt.init_app(app)
    db.init_app(app)
    from . import routes
    routes.init_app(app)
    return app