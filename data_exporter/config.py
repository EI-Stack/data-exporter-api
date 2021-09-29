import os


class Config:
    EKS_URL = os.getenv("EKS_URL")
    AFS_URL = os.getenv("AFS_URL")
    S3_ENDPOINT = os.getenv("S3_ENDPOINT")
    S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
    S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")
    INSTANCE_ID = os.getenv("INSTANCE_ID")
    X_IFP_APP_SECRET = os.getenv("X_IFP_APP_SECRET")
    SSO_TOKEN = os.getenv("SSO_TOKEN")
    SCHEDULER_API_ENABLED = True
    JOBS = [
        {
            'id': 'spc_data',                # 一个标识
            'func': 'data_exporter.utils.dataset_helper:spc_routine',     # 指定运行的函数
            'args': None,              # 传入函数的参数
            'trigger': 'cron',       # 指定 定时任务的类型
            'day': '*',
            'hour': '*',
            'minute': '0, 15, 30, 45'      # 运行的间隔时间
        }
    ]

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    MQTT_BROKER_URL = os.getenv("MQTT_BROKER_URL")
    MQTT_BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", 31883))
    MQTT_REFRESH_TIME = float(os.getenv("MQTT_REFRESH_TIME", 1.0))
    MQTT_USERNAME = os.getenv("MQTT_USERNAME")
    MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")
    MQTT_KEEPALIVE = int(os.getenv("MQTT_KEEPALIVE", 5))
    MQTT_TLS_ENABLED = False
    MONGODB_SETTINGS = {
        "db": os.getenv("MONGODB_TABLE_NAME"),
        "host": os.getenv("MONGODB_HOST"),
        "port": int(os.getenv("MONGODB_PORT")),
    }


config = {"development": DevelopmentConfig}
