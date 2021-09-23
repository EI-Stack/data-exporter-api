from uuid import uuid4
from datetime import datetime, timedelta
from flask import Blueprint, request, current_app, jsonify
# from data_exporter import mqtt
from data_exporter.utils.mqtt_topic import MqttTopicHandler
from io import BytesIO
import json
import pandas as pd
import threading
from data_exporter.utils.dataset_helper import transfer_to_big_parameter_id, split_datetime
from data_exporter.utils.csv_value_helper import complement_csv_value
from data_exporter.utils.web_client import DataSetWebClient

# print(mqtt.broker_url)
dataset_bp = Blueprint("dataset_bp", __name__)


# @mqtt.on_connect()
# def handle_connect(client, userdata, flags, rc):
#     # mqtt.subscribe('iot-2/evt/waconn/fmt/grant-test')
#     mqtt.subscribe("iot-2/evt/wadata/fmt/grant-test")
#     mqtt.subscribe("iot-2/evt/wacfg/fmt/grant-test")
#     # print(mqtt.topics)
#
#
# @mqtt.on_message()
# def handle_mqtt_message(client, userdata, message):
#     payload = message.payload.decode()
#     res_dict = json.loads(payload)
#     print("-------msg-------")
#     print("dict  :", res_dict, "<<<>>>", "topic  :", message.topic)
#     topic_type = message.topic.split("/")[2]
#     if topic_type == "waconn":
#         MqttTopicHandler(res_dict).waconn_info()
#     elif topic_type == "wadata":
#         MqttTopicHandler(res_dict).wadata_info()
#     elif topic_type == "wacfg":
#         MqttTopicHandler(res_dict).wacfg_info()
#     # elif topic_type == 'ifpcfg':
#     #     MqttTopicHandler(res_dict).ifpcfg_info()


# mqtt.client.on_connect = handle_connect
# mqtt.client.on_message = handle_mqtt_message
# print("mqtt_set")
# mqtt.client.loop_forever()
# mqtt.client.loop()

S3_bucket_name = "data-exporter-file"


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
    normalized_all = pd.DataFrame()
    for i, date in enumerate(date_list):
        variables = {"id": parameter_id, "from": date[0], "to": date[1]}
        r = DataSetWebClient.get_dataset_with_graphql_by_date(variables)
        data = pd.read_json(r.text)["data"]["parameter"]
        normalized = pd.json_normalize(data, "valuesInRange", ["scadaId", "tagId"])
        print(normalized.index, date[0], date[1])
        normalized_all = pd.concat([normalized_all, normalized], axis=0, ignore_index=True)
    print(normalized_all)
    # print(r.text)
    normalized_df = complement_csv_value(normalized_all)
    print(normalized_df)
    if datetime.fromtimestamp(
        normalized_df.tail(1)["savedAt"] / 1000
    ) - datetime.fromtimestamp(normalized_df.head(1)["savedAt"] / 1000) < timedelta(
        days=30
    ):
        return (
            jsonify(
                {
                    "message": "Data Exporter dataset is less than one month of information"
                },
            ),
            406,
        )
    columns = normalized_df.columns
    if "num" in columns:
        target = "num"
    else:
        target = "value"
    csv_bytes = normalized_df.to_csv().encode("utf-8")
    csv_buffer = BytesIO(csv_bytes)
    client = DataSetWebClient.get_minio_client(S3_bucket_name)
    file_name = parameter_id + "." + str(uuid4())[-9:-1]
    client.put_object(
        S3_bucket_name,
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
                if data.get("bucket") == S3_bucket_name:
                    files = data.get("blobs").get("files")
                    files.append(f"{file_name}.csv")
            # put file
            DataSetWebClient().put_dataset_config(
                dataset_uuid=item.get("uuid"), payload=payload
            )
            exist = True
            break
    if not exist:
        payload = {
            "name": data_set_name,
            "firehose": {
                "type": "s3-firehose",
                "data": {
                    "dbType": "external",
                    "serviceName": "",
                    "serviceKey": "",
                    "endPoint": f"https://{current_app.config['S3_ENDPOINT']}:443",
                    "accessKey": current_app.config["S3_ACCESS_KEY"],
                    "secretAccessKey": current_app.config["S3_SECRET_KEY"],
                    "buckets": [
                        {
                            "blobs": {"files": [f"{file_name}.csv"], "folders": []},
                            "bucket": S3_bucket_name,
                        }
                    ],
                },
            },
            "sample_data": "",
            "datasource": "s3-firehose",
        }
        r = DataSetWebClient().post_dataset_bucket(payload=payload)
        dataset_id = json.loads(r.text).get("uuid")
    data_dict = {
        "data": {
            "bucket": S3_bucket_name,
            "file": f"{file_name}.csv",
            "dataset_id": dataset_id,
            "target": target,
        }
    }
    return data_dict
