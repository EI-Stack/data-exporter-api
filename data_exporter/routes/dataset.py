from uuid import uuid4
from datetime import datetime, timedelta
from flask import Blueprint, request, current_app, jsonify

from data_exporter import mqtt
from data_exporter.utils.mqtt_topic import MqttTopicHandler
from io import BytesIO
import json
import pandas as pd
import threading
from data_exporter.utils.dataset_helper import (
    transfer_to_big_parameter_id,
    split_datetime,
    set_s3_dataset,
    concat_split_datetime_dataset,
)
from data_exporter.utils.csv_value_helper import complement_csv_value, check_data_count
from data_exporter.utils.web_client import DataSetWebClient

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

s3_bucket_name = "data-exporter-file"


@dataset_bp.route("/dataset/<parameter_id>", methods=["GET"])
def get_dataset_file(parameter_id):
    if not parameter_id:
        raise ValueError("Can not Find parameter_id")
    parameter_id = transfer_to_big_parameter_id(parameter_id)
    data_set_name = request.args.get("dataset_name")
    if not data_set_name:
        raise ValueError("Can not Find dataset_name with parameter")
    # variables = {"id": parameter_id, "n": 50000}  # pow(2, 31) - 1
    end = datetime.utcnow()
    start = end - timedelta(days=100)
    date_list = split_datetime(start, end)
    normalized_all = concat_split_datetime_dataset(date_list, parameter_id)
    normalized_df, target = complement_csv_value(normalized_all)
    if not check_data_count(normalized_df):
        return (
            jsonify(
                {"message": "Dataset is less than one month"},
            ),
            406,
        )
    csv_bytes = normalized_df.to_csv().encode("utf-8")
    csv_buffer = BytesIO(csv_bytes)
    client = DataSetWebClient.get_minio_client(s3_bucket_name)
    file_name = parameter_id + "." + str(uuid4())[-9:-1]
    client.put_object(
        s3_bucket_name,
        f"{file_name}.csv",
        data=csv_buffer,
        length=len(csv_bytes),
        content_type="application/csv",
    )
    res = DataSetWebClient().get_dataset_information()
    data = json.loads(res.text)
    exist = False
    dataset_id = ""
    for item in data.get("resources"):
        if item.get("name") == data_set_name:
            dataset_id = item.get("uuid")
            f = DataSetWebClient().get_dataset_config(item.get("uuid"))
            payload = json.loads(f.text)
            for data in payload.get("firehose").get("data").get("buckets"):
                if data.get("bucket") == s3_bucket_name:
                    files = data.get("blobs").get("files")
                    files.append(f"{file_name}.csv")
            # put file
            DataSetWebClient().put_dataset_config(
                dataset_uuid=item.get("uuid"), payload=payload
            )
            exist = True
            break
    if not exist:
        dataset_id = set_s3_dataset(
            current_app, data_set_name, file_name, s3_bucket_name
        )
    data_dict = {
        "data": {
            "bucket": s3_bucket_name,
            "file": f"{file_name}.csv",
            "dataset_id": dataset_id,
            "target": target,
        }
    }
    return data_dict
