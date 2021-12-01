from uuid import uuid4
from datetime import datetime, timedelta
from flask import Blueprint, request, current_app, jsonify

from data_exporter import mqtt
from data_exporter.utils.mqtt_topic import MqttTopicHandler
from data_exporter.config import Config
from io import BytesIO
import json
from data_exporter.utils.dataset_helper import (
    transfer_to_big_parameter_id,
    split_datetime,
    set_blob_dataset,
    concat_split_datetime_dataset,
)
from data_exporter.utils.csv_value_helper import (
    complement_csv_value,
    check_data_count,
    check_target,
    complement_dataset_value,
)
from data_exporter.utils.web_client import DataSetWebClient, AzureBlob, EnsaasMongoDB
import pandas as pd

# print(mqtt.broker_url)
dataset_bp = Blueprint("dataset_bp", __name__)


@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    # mqtt.subscribe('iot-2/evt/waconn/fmt/grant-test')
    mqtt.subscribe("iot-2/evt/wadata/fmt/grant-test")
    mqtt.subscribe("iot-2/evt/wacfg/fmt/grant-test")
    # print(mqtt.topics)


@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    payload = message.payload.decode()
    res_dict = json.loads(payload)
    print("-------msg-------")
    print("dict  :", res_dict, "<<<>>>", "topic  :", message.topic)
    topic_type = message.topic.split("/")[2]
    if topic_type == "waconn":
        MqttTopicHandler(res_dict).waconn_info()
    elif topic_type == "wadata":
        MqttTopicHandler(res_dict).wadata_info()
    elif topic_type == "wacfg":
        MqttTopicHandler(res_dict).wacfg_info()
    # elif topic_type == 'ifpcfg':
    #     MqttTopicHandler(res_dict).ifpcfg_info()


mqtt.client.on_connect = handle_connect
mqtt.client.on_message = handle_mqtt_message
# print("mqtt_set")
# mqtt.client.loop_forever()
# mqtt.client.loop()

blob_bucket_name = current_app.config["S3_BUCKET_NAME"]
DATA_LENGTH = 2880


@dataset_bp.route("/dataset/<task_name>", methods=["GET"])
def get_dataset_file(task_name):
    if not task_name:
        raise ValueError("Can not Find task_name")
    data_set_name = request.args.get("dataset_name")
    if not data_set_name:
        raise ValueError("Can not Find dataset_name with parameter")
    data_set_name = data_set_name.replace(" ", "_")
    mongo = EnsaasMongoDB()
    mongo_db = mongo.DATABASE["iii.pml.task"]
    if not mongo_db:
        return (
            jsonify(
                {"message": "Can not Find collection named 'iii.pml.task'"},
            ),
            406,
        )
    azure_conn = Config.get_env_res("AZURE_STORAGE_CONNECTION")
    end = datetime.utcnow()
    start = end - timedelta(days=100)
    cursor = mongo_db.find({"TaskName": task_name})
    data_list = list(cursor)
    df_all = pd.DataFrame()
    for data in data_list:
        print(data.get("ParameterID"))
        if data.get("UsageType") == "EnergyDemand":
            collection = "ifp.core.kw_real_time"
        elif data.get("UsageType") == "EnergyConsumption":
            collection = "ifp.core.kwh_real_time"
        else:
            return (
                jsonify(
                    {"message": "Data is not found in 'UsageType'"},
                ),
                404,
            )
        mongo_db = mongo.DATABASE[collection]
        cursor = mongo_db.find(
            {
                "parameterNodeId": data.get("ParameterID"),
                "logTime": {"$gte": start, "$lt": end},
            }
        )
        data = list(cursor)
        print(len(data))
        if len(data) < DATA_LENGTH:
            continue
        df = pd.DataFrame(data)
        # normalized_df = complement_dataset_value(df,target)
        print("-" * 30)
        df_all = pd.concat([df_all, df], ignore_index=True)
    print(df_all)
    target = check_target(df_all)
    file_name = task_name + "." + str(uuid4())[-9:-1]
    file_name = file_name.replace(" ", "_")
    df_all.to_csv(f"./csv_file/{file_name}.csv", encoding="utf-8")
    csv_bytes = df_all.to_csv().encode("utf-8")
    csv_buffer = BytesIO(csv_bytes)
    azure_blob = AzureBlob(azure_conn)
    azure_blob.UploadFile(blob_bucket_name, "./csv_file", f"{file_name}.csv")
    if f"{file_name}.csv" not in azure_blob.ListBlob(blob_bucket_name):
        return (
            jsonify(
                {"message": "The file is not in Azure Blob ."},
            ),
            404,
        )
    dataset_web_client = DataSetWebClient()
    res = dataset_web_client.get_dataset_information()
    data = json.loads(res.text)
    exist = False
    dataset_id = ""
    if not data.get("resources"):
        return {"data": {"bucket": blob_bucket_name}}
    for item in data.get("resources"):
        if item.get("name") == data_set_name:
            dataset_id = item.get("uuid")
            f = dataset_web_client.get_dataset_config(item.get("uuid"))
            payload = json.loads(f.text)
            if not payload.get("firehose").get("data").get("containers"):
                return (
                    jsonify(
                        {"message": "Wrong bucket is about 'Blob'"},
                    ),
                    404,
                )
            for data in payload.get("firehose").get("data").get("containers"):
                if data.get("container") == blob_bucket_name:
                    files = data.get("blobs").get("files")
                    files.append(f"{file_name}.csv")
            # put file
            dataset_web_client.put_dataset_config(
                dataset_uuid=item.get("uuid"), payload=payload
            )
            exist = True
            break
    if not exist:
        dataset_id = set_blob_dataset(data_set_name, file_name, blob_bucket_name)
    data_dict = {
        "data": {
            "bucket": blob_bucket_name,
            "file": f"{file_name}.csv",
            "dataset_id": dataset_id,
            "target_col": target,
            "index_col": "logTime",
        }
    }
    return data_dict


# @dataset_bp.route("/dataset/<parameter_id>", methods=["GET"])
# def get_dataset_file(parameter_id):
#     if not parameter_id:
#         raise ValueError("Can not Find parameter_id")
#     dataset_web_client = DataSetWebClient()
#     # parameter_id = transfer_to_big_parameter_id(parameter_id)
#     data_set_name = request.args.get("dataset_name")
#     if not data_set_name:
#         raise ValueError("Can not Find dataset_name with parameter")
#     end = datetime.utcnow()
#     start = end - timedelta(days=100)
#     date_list = split_datetime(start, end)
#     normalized_all = concat_split_datetime_dataset(date_list, parameter_id)
#     if normalized_all.empty:
#         return {"data": {"bucket": blob_bucket_name}}
#     target = check_target(normalized_all)
#     normalized_df = complement_csv_value(normalized_all, target)
#     if not check_data_count(normalized_df):
#         return (
#             jsonify(
#                 {"message": "Dataset is less than one month"},
#             ),
#             406,
#         )
#     file_name = parameter_id + "." + str(uuid4())[-9:-1]
#     normalized_df.to_csv(f"./csv_file/{file_name}.csv", encoding="utf-8")
#     csv_bytes = normalized_df.to_csv().encode("utf-8")
#     csv_buffer = BytesIO(csv_bytes)
#     azure_blob = AzureBlob(Config.get_env_res("AZURE_STORAGE_CONNECTION"))
#     azure_blob.UploadFile(blob_bucket_name, "./csv_file", f"{file_name}.csv")
#     res = dataset_web_client.get_dataset_information()
#     data = json.loads(res.text)
#     exist = False
#     dataset_id = ""
#     if not data.get("resources"):
#         return {"data": {"bucket": blob_bucket_name}}
#     for item in data.get("resources"):
#         if item.get("name") == data_set_name:
#             dataset_id = item.get("uuid")
#             f = dataset_web_client.get_dataset_config(item.get("uuid"))
#             payload = json.loads(f.text)
#             for data in payload.get("firehose").get("data").get("containers"):
#                 if data.get("container") == blob_bucket_name:
#                     files = data.get("blobs").get("files")
#                     files.append(f"{file_name}.csv")
#             # put file
#             dataset_web_client.put_dataset_config(
#                 dataset_uuid=item.get("uuid"), payload=payload
#             )
#             exist = True
#             break
#     if not exist:
#         dataset_id = set_blob_dataset(data_set_name, file_name, blob_bucket_name)
#     data_dict = {
#         "data": {
#             "bucket": blob_bucket_name,
#             "file": f"{file_name}.csv",
#             "dataset_id": dataset_id,
#             "target_col": target,
#             "index_col": "logTime"
#         }
#     }
#     return data_dict
