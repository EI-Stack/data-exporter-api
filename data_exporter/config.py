import logging
import os
import json


class Config:
    IFP_DESK_API_URL = os.getenv("IFP_DESK_API_URL")
    AFS_URL = os.getenv("AFS_DEVELOPMENT_SERVICE_API_URL")
    S3_ENDPOINT = os.getenv("S3_ENDPOINT", "ai-storage.amp.iii-ei-stack.com")
    S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "Bknu1IKIfK5it1XnseDh4GsuzwhAG1JF")
    S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "mSM8eEYrT57votdHj7BPmZdxvN5hSb3I")
    S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "data-exporter-file")
    INSTANCE_ID = os.getenv("INSTANCE_ID", "2174f980-0fc1-5b88-913b-2db9c1deccc5")
    IFP_DESK_CLIENT_SECRET = os.getenv("IFP_DESK_CLIENT_SECRET")
    SSO_TOKEN = os.getenv("IFPS_PREDICT_RETRAIN_API_URL") + "/api/v1/token"
    IFP_DESK_USERNAME = os.getenv("IFP_DESK_USERNAME")
    IFP_DESK_PASSWORD = os.getenv("IFP_DESK_PASSWORD")
    SCHEDULER_API_ENABLED = True

    if os.getenv("ENSAAS_SERVICES") is not None:
        ENSAAS_SERVICES = json.loads(os.getenv("ENSAAS_SERVICES"))
        MONGODB_URL = ENSAAS_SERVICES["mongodb"][0]["credentials"]["externalHosts"]
        MONGODB_USERNAME = ENSAAS_SERVICES["mongodb"][0]["credentials"]["username"]
        MONGODB_PASSWORD = ENSAAS_SERVICES["mongodb"][0]["credentials"]["password"]
        MONGODB_DATABASE = ENSAAS_SERVICES["mongodb"][0]["credentials"]["database"]
        MONGODB_AUTH_SOURCE = MONGODB_DATABASE
    else:
        MONGODB_URL = os.getenv("MONGODB_URL")
        MONGODB_USERNAME = os.getenv("MONGODB_USERNAME")
        MONGODB_DATABASE = os.getenv("MONGODB_DATABASE")
        MONGODB_AUTH_SOURCE = os.getenv("MONGODB_AUTH_SOURCE")
        MONGODB_PASSWORD = os.getenv("MONGODB_PASSWORD")
        if MONGODB_PASSWORD is None:
            MONGODB_PASSWORD_FILE = os.getenv("MONGODB_PASSWORD_FILE")
        try:
            secret_fpath = f"/run/secrets/mongo-root_password"
            existence = os.path.exists(secret_fpath)
            if existence:
                ret = open(secret_fpath).read().rstrip("\n")
                logging.info("[MONGODB_PASSWORD] -------->   " + ret)
                MONGODB_PASSWORD = ret
        except Exception as e:
            raise EnvironmentError(e)
    JOBS = [
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
        },
    ]

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    # MQTT_BROKER_URL = os.getenv("MQTT_BROKER_URL")
    # MQTT_BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", 31883))
    # MQTT_REFRESH_TIME = float(os.getenv("MQTT_REFRESH_TIME", 1.0))
    # MQTT_USERNAME = os.getenv("MQTT_USERNAME")
    # MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")
    # MQTT_KEEPALIVE = int(os.getenv("MQTT_KEEPALIVE", 5))
    # MQTT_TLS_ENABLED = False
    # MONGODB_SETTINGS = [
    #     {
    #         "db": os.getenv("MONGODB_TABLE_NAME"),
    #         "host": os.getenv("MONGODB_HOST"),
    #         "port": int(os.getenv("MONGODB_PORT")),
    #     }
    # ]


config = {"development": DevelopmentConfig}
