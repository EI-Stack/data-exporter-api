import os


class Config:
    EKS_URL = "https://ifp-organizer-dmd-eks009.sa.wise-paas.com/graphql"

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    MQTT_BROKER_URL = 'ifactory-mqtt.iii-ei-stack.com'
    MQTT_BROKER_PORT = 31883
    MQTT_REFRESH_TIME = 1.0
    MQTT_USERNAME = 'iii-eistack'
    MQTT_PASSWORD = 'g0kBqOviZ8'
    MQTT_KEEPALIVE = 5
    MQTT_TLS_ENABLED = False
    # MONGO_URI = "mongodb://localhost:27017/data_set"
    MONGODB_SETTINGS = {
        'db': 'data_set',
        'host': 'localhost',
        'port': 27017
    }


config = {
    'development': DevelopmentConfig
}
