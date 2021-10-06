import logging
import os
import json


class Config:
    EKS_URL = os.getenv("EKS_URL")
    AFS_URL = os.getenv("AFS_URL")
    S3_ENDPOINT = os.getenv("S3_ENDPOINT")
    S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
    S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")
    S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
    INSTANCE_ID = os.getenv("INSTANCE_ID")
    X_IFP_APP_SECRET = os.getenv("X_IFP_APP_SECRET")
    SSO_TOKEN = os.getenv("SSO_TOKEN")
    SCHEDULER_API_ENABLED = True
    JOBS = [
        # {
        #     "id": "spc_data",  # 一个标识
        #     "func": "data_exporter.utils.dataset_helper:spc_routine",  # 指定运行的函数
        #     "args": None,  # 传入函数的参数
        #     "trigger": "cron",  # 指定 定时任务的类型
        #     "day": "*",
        #     "hour": "*",
        #     "minute": "0, 15, 30, 45",  # 运行的间隔时间
        # },
        {
            "id": "clean_csv",  # 一个标识
            "func": "data_exporter.utils.csv_value_helper:clean_csv",  # 指定运行的函数
            "args": None,  # 传入函数的参数
            "trigger": "cron",  # 指定 定时任务的类型
            "day": "*",
            "hour": "*",
        },
        {
            "id": "predict_data_metric",  # 一个标识
            "func": "data_exporter.utils.dataset_helper:predict_data_metric",  # 指定运行的函数
            "args": None,  # 传入函数的参数
            "trigger": "cron",  # 指定 定时任务的类型
            "day": "*",
            "hour": "*",
            "minute": "*"
        },
    ]
    if os.getenv("ENSAAS_SERVICES") is not None:
        ENSAAS_SERVICES = json.loads(os.getenv("ENSAAS_SERVICES"))
        ENSAAS_MONGODB_URL = ENSAAS_SERVICES["mongodb"][0]["credentials"][
            "externalHosts"
        ]
        ENSAAS_MONGODB_USERNAME = ENSAAS_SERVICES["mongodb"][0]["credentials"][
            "username"
        ]
        ENSAAS_MONGODB_PASSWORD = ENSAAS_SERVICES["mongodb"][0]["credentials"][
            "password"
        ]
        ENSAAS_MONGODB_DATABASE = ENSAAS_SERVICES["mongodb"][0]["credentials"][
            "database"
        ]
        ENSAAS_MONGODB_AUTH_SOURCE = ENSAAS_MONGODB_DATABASE
    else:
        ENSAAS_MONGODB_URL = os.getenv("MONGODB_URL")
        ENSAAS_MONGODB_USERNAME = os.getenv("MONGODB_USERNAME")
        ENSAAS_MONGODB_DATABASE = os.getenv("MONGODB_DATABASE")
        ENSAAS_MONGODB_AUTH_SOURCE = os.getenv("MONGODB_AUTH_SOURCE")
        ENSAAS_MONGODB_PASSWORD_FILE = os.getenv("MONGODB_PASSWORD_FILE")
        try:
            secret_fpath = f"/run/secrets/mongo-root_password"
            existence = os.path.exists(secret_fpath)
            if existence:
                ret = open(secret_fpath).read().rstrip("\n")
                logging.info("[MONGODB_PASSWORD] -------->   " + ret)
                MONGODB_PASSWORD = ret
        except Exception as e:
            raise EnvironmentError(e)
    EKS_009_HOST = os.getenv("EKS_009_HOST")
    EKS_009_USERNAME = os.getenv("EKS_009_USERNAME")
    EKS_009_PASSWORD = os.getenv("EKS_009_PASSWORD")
    EKS_009_DATABASE = os.getenv("EKS_009_DATABASE")

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
    MONGODB_SETTINGS = [
        {
            "db": os.getenv("MONGODB_TABLE_NAME"),
            "host": os.getenv("MONGODB_HOST"),
            "port": int(os.getenv("MONGODB_PORT")),
        }
    ]


config = {"development": DevelopmentConfig}
