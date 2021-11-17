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
    # try:
    #     r = requests.get(os.getenv("IFPS_PREDICT_RETRAIN_API_URL") + "/api/v1/auth/me")
    # except:
    #     print("Can not get environment response.")
    # if r.status_code == 200:
    #     res_env = json.loads(r.text)
    #     INSTANCE_ID = res_env.get("AFS_INSTANCESID")
    #     AZURE_STORAGE_CONNECTION = res_env.get("AZURE_STORAGE_CONNECTION")
    #     AZURE_STORAGE_ACCOUNT_NAME = res_env.get("AZURE_STORAGE_ACCOUNT_NAME")
    #     AZURE_STORAGE_ACCOUNT_KEY = res_env.get("AZURE_STORAGE_ACCOUNT_KEY")
    #     SSO_TOKEN = "Bearer " + res_env.get("Authorization")
    #     AFS_URL = res_env.get("AFS_API_URL")
    #     IFP_DESK_CLIENT_SECRET = res_env.get("IFP_DESK_CLIENT_SECRET")
    # else:
    #     AFS_URL = os.getenv("AFS_DEVELOPMENT_SERVICE_API_URL")
    #     INSTANCE_ID = os.getenv("INSTANCE_ID", "2174f980-0fc1-5b88-913b-2db9c1deccc5")
    #     # r = requests.get(os.getenv("IFPS_PREDICT_RETRAIN_API_URL" + "/api/v1/token"))
    #     SSO_TOKEN = json.loads(r.text).get("Authorization")
    if os.getenv("ENSAAS_SERVICES") is not None:
        ENSAAS_SERVICES = json.loads(os.getenv("ENSAAS_SERVICES"))
        MONGODB_URL = ENSAAS_SERVICES["mongodb"][0]["credentials"]["externalHosts"]
        MONGODB_USERNAME = ENSAAS_SERVICES["mongodb"][0]["credentials"]["username"]
        MONGODB_PASSWORD = ENSAAS_SERVICES["mongodb"][0]["credentials"]["password"]
        MONGODB_DATABASE = ENSAAS_SERVICES["mongodb"][0]["credentials"]["database"]
        MONGODB_AUTH_SOURCE = MONGODB_DATABASE
        if not res_env.get("IFP_DESK_CLIENT_SECRET"):
            IFP_DESK_CLIENT_SECRET = os.getenv('IFP_DESK_CLIENT_SECRET')
    else:
        MONGODB_URL = os.getenv("MONGODB_URL")
        MONGODB_USERNAME = os.getenv("MONGODB_USERNAME")
        MONGODB_DATABASE = os.getenv("MONGODB_DATABASE")
        MONGODB_AUTH_SOURCE = os.getenv("MONGODB_AUTH_SOURCE")
        MONGODB_PASSWORD = os.getenv("MONGODB_PASSWORD")
        MONGODB_PASSWORD_FILE = os.getenv('MONGODB_PASSWORD_FILE')
        if not res_env.get("IFP_DESK_CLIENT_SECRET"):
            IFP_DESK_CLIENT_SECRET = os.getenv('IFP_DESK_CLIENT_SECRET')
        try:
            secret_fpath = f'/run/secrets/mongo-root_password'
            existence = os.path.exists(secret_fpath)
            if existence:
                ret = open(secret_fpath).read().rstrip('\n')
                print("[MONGODB_PASSWORD] -------->   ", ret)
                MONGODB_PASSWORD = ret
        except:
            print("[MONGODB_PASSWORD_FILE] --------> GET ERROR!!!")
        try:
            secret_fpath = f'/run/secrets/ifp-app_secret'
            existence = os.path.exists(secret_fpath)
            if existence:
                ret = open(secret_fpath).read().rstrip('\n')
                print("[IFP_DESK_CLIENT_SECRET] -------->   ", ret)
                IFP_DESK_CLIENT_SECRET = ret
        except:
            print("[IFP_DESK_CLIENT_SECRET] --------> GET ERROR!!!")

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
            "hour": "1",
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
