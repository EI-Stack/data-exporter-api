import logging
import os
import json
import requests
from flask import jsonify, abort, Response, make_response


class Config:
    res_env = {}
    S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "data-exporter-file")
    IFP_DESK_USERNAME = os.getenv("IFP_DESK_USERNAME")
    IFP_DESK_PASSWORD = os.getenv("IFP_DESK_PASSWORD")
    IFP_DESK_API_URL = os.getenv("IFP_DESK_API_URL")
    SCHEDULER_API_ENABLED = True
    IFP_DESK_CLIENT_SECRET = os.environ.get('IFP_DESK_CLIENT_SECRET')

    MONGODB_URL = os.environ.get('MONGODB_URL')
    MONGODB_USERNAME = os.environ.get('MONGODB_USERNAME')
    MONGODB_DATABASE = os.environ.get('MONGODB_DATABASE')
    MONGODB_AUTH_SOURCE = os.environ.get('MONGODB_AUTH_SOURCE')
    MONGODB_PASSWORD = os.environ.get('MONGODB_PASSWORD')
    MONGODB_PASSWORD_FILE = os.environ.get('MONGODB_PASSWORD_FILE')
    MONGODB_AUTHMECHANISM = os.environ.get('MONGODB_AUTHMECHANISM', "SCRAM-SHA-1")

    POSTGRES_URL = os.environ.get('POSTGRES_URL')
    POSTGRES_USERNAME = os.environ.get('POSTGRES_USERNAME')
    POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD')
    POSTGRES_DATABASE = os.environ.get('POSTGRES_DATABASE')
    POSTGRES_PASSWORD_FILE = os.environ.get('POSTGRES_PASSWORD_FILE')

    REDIS_URL = os.environ.get('REDIS_URL')
    REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD')
    REDIS_PASSWORD_FILE = os.environ.get('REDIS_PASSWORD_FILE')
    REDIS_DATABASE = os.environ.get('REDIS_DATABASE', "ifp_redis")

    CLUSTER = os.environ.get('cluster')
    NAMESPACE = os.environ.get('namespace')
    EXTERNAL = os.environ.get('external')
    WORKSPACE = os.environ.get('workspace')
    INFERENCE_API_URL = os.environ.get('IFPS_PREDICT_INFERENCE_API_URL')
    RETRAIN_API_URL = os.environ.get('IFPS_PREDICT_RETRAIN_API_URL')
    """ Clound Database env get """
    ENSAAS_SERVICES = os.getenv("ENSAAS_SERVICES")
    if ENSAAS_SERVICES is not None:
        ENSAAS_SERVICES = json.loads(ENSAAS_SERVICES)
        if 'mongodb' in ENSAAS_SERVICES:
            MONGODB_URL = ENSAAS_SERVICES['mongodb'][0]['credentials']['externalHosts']
            MONGODB_USERNAME = ENSAAS_SERVICES['mongodb'][0]['credentials']['username']
            MONGODB_PASSWORD = ENSAAS_SERVICES['mongodb'][0]['credentials']['password']
            MONGODB_DATABASE = ENSAAS_SERVICES['mongodb'][0]['credentials']['database']
            MONGODB_AUTH_SOURCE = MONGODB_DATABASE
        if 'postgresql' in ENSAAS_SERVICES:
            POSTGRES_URL = ENSAAS_SERVICES['postgresql'][0]['credentials']['externalHosts']
            POSTGRES_USERNAME = ENSAAS_SERVICES['postgresql'][0]['credentials']['username']
            POSTGRES_PASSWORD = ENSAAS_SERVICES['postgresql'][0]['credentials']['password']
            POSTGRES_DATABASE = ENSAAS_SERVICES['postgresql'][0]['credentials']['database']
        if 'redis' in ENSAAS_SERVICES:
            REDIS_HOST = ENSAAS_SERVICES['postgresql'][0]['credentials']['host']
            REDIS_PORT = str(ENSAAS_SERVICES['postgresql'][0]['credentials']['port'])
            REDIS_URL = REDIS_HOST + ":" + REDIS_PORT
            REDIS_PASSWORD = ENSAAS_SERVICES['postgresql'][0]['credentials']['password']

    """ Local password file get """
    if MONGODB_PASSWORD == None and MONGODB_PASSWORD_FILE is not None:
        existence = os.path.exists(MONGODB_PASSWORD_FILE)
        if existence:
            MONGODB_PASSWORD = open(MONGODB_PASSWORD_FILE).read().rstrip('\n')
    if POSTGRES_PASSWORD == None and POSTGRES_PASSWORD_FILE is not None:
        existence = os.path.exists(POSTGRES_PASSWORD_FILE)
        if existence:
            POSTGRES_PASSWORD = open(POSTGRES_PASSWORD_FILE).read().rstrip('\n')
    if REDIS_PASSWORD == None and REDIS_PASSWORD_FILE is not None:
        existence = os.path.exists(REDIS_PASSWORD_FILE)
        if existence:
            REDIS_PASSWORD = open(REDIS_PASSWORD_FILE).read().rstrip('\n')
    if IFP_DESK_CLIENT_SECRET is not None:
        try:
            IFP_DESK_CLIENT_SECRET = open(IFP_DESK_CLIENT_SECRET).read().rstrip('\n')
        except:
            IFP_DESK_CLIENT_SECRET = IFP_DESK_CLIENT_SECRET
        IFP_DESK_HEADERS = {'X-Ifp-App-Secret': IFP_DESK_CLIENT_SECRET}

    """ Clound auto combine URL """
    if IFP_DESK_API_URL is None and EXTERNAL is not None:
        IFP_DESK_API_URL = "https://ifp-organizer-" + NAMESPACE + "-" + CLUSTER + "." + EXTERNAL + "/graphql"
    if INFERENCE_API_URL is None and EXTERNAL is not None:
        INFERENCE_API_URL = "https://ifps-predict-inference-" + NAMESPACE + "-" + CLUSTER + "." + EXTERNAL
    if RETRAIN_API_URL is None and EXTERNAL is not None:
        RETRAIN_API_URL = "https://ifps-predict-train-" + NAMESPACE + "-" + CLUSTER + "." + EXTERNAL

    JOBS = [
        {
            "id": "clean_csv",  # 一个标识
            "func": "data_exporter.utils.csv_value_helper:clean_csv",  # 指定运行的函数
            "args": None,  # 传入函数的参数
            "trigger": "cron",  # 指定 定时任务的类型
            "day": "*",
            "hour": "1",
        },
        {
            "id": "predict_data_metric",  # 一个标识
            "func": "data_exporter.utils.dataset_helper:predict_data_metric",  # 指定运行的函数
            "args": None,  # 传入函数的参数
            "trigger": "cron",  # 指定 定时任务的类型
            "day": "*",
            "hour": "2",
        },
    ]

    @staticmethod
    def init_app(app):
        pass

    @staticmethod
    def get_env_res(key):
        try:
            r = requests.get(os.getenv("IFPS_PREDICT_RETRAIN_API_URL") + "/api/v1/auth/me")
            if r.status_code == 200:
                res_env = json.loads(r.text)
                if key == "Authorization":
                    return "Bearer " + res_env.get("Authorization")
                return res_env.get(key)
            else:
                status = r.status_code
                text = json.loads(r.text)
                abort(make_response(jsonify(text), status))
        except requests.exceptions.HTTPError as e:
            # Whoops it wasn't a 200
            return "Error: " + str(e)

        # AFS_URL = os.getenv("AFS_DEVELOPMENT_SERVICE_API_URL")
        # INSTANCE_ID = os.getenv("INSTANCE_ID", "2174f980-0fc1-5b88-913b-2db9c1deccc5")
        # # r = requests.get(os.getenv("IFPS_PREDICT_RETRAIN_API_URL" + "/api/v1/token"))
        # SSO_TOKEN = json.loads(r.text).get("Authorization")


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
