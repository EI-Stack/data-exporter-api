from flask import Blueprint, request, current_app
from data_exporter import mqtt
from data_exporter.utils.mqtt_topic import MqttTopicHandler
from io import BytesIO
import json
import pandas as pd

from data_exporter.utils.web_client import DataSetWebClient

print(mqtt.broker_url)
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
print("mqtt_set")
# mqtt.client.loop_forever()
# mqtt.client.loop()


@dataset_bp.route("/dataset/<parameter_id>", methods=["GET"])
def get_dataset_file(parameter_id):
    if not parameter_id:
        raise ValueError("Can not Find parameter_id")
    data_set_name = request.args.get("dataset_name")
    if not data_set_name:
        raise ValueError("Can not Find dataset_name with parameter")
    variables = {"id": parameter_id, "n": 10}  # pow(2, 31) - 1
    r = DataSetWebClient().get_dataset_with_graphql(variables)
    data = pd.read_json(r.text)["data"]["parameter"]
    normalized = pd.json_normalize(data, "limitToNthValues", ["scadaId", "tagId"])
    csv_bytes = normalized.to_csv().encode("utf-8")
    csv_buffer = BytesIO(csv_bytes)
    client = DataSetWebClient.get_minio_client()
    client.put_object(
        "test-grant",
        "test456-grant.csv",
        data=csv_buffer,
        length=len(csv_bytes),
        content_type="application/csv",
    )
    res = DataSetWebClient().get_dataset_information()
    data = json.loads(res.text)
    exist = False
    for item in data.get('resources'):
        if item.get('name') == data_set_name:
            f = DataSetWebClient().get_dataset_config(item.get('uuid'))
            payload = json.loads(f.text)
            for data in payload.get('firehose').get('data').get('buckets'):
                if data.get('bucket') == "test-grant":
                    files = data.get('blobs').get('files')
                    files.append('test456-grant.csv')
            # put file
            DataSetWebClient().put_dataset_config(dataset_uuid=item.get('uuid'), payload=payload)
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
                        "accessKey": current_app.config['S3_ACCESS_KEY'],
                        "secretAccessKey": current_app.config['S3_SECRET_KEY'],
                        "buckets": [
                            {
                                "blobs": {
                                    "files": ["test456-grant.csv"],
                                    "folders": []
                                },
                                "bucket": "test-grant"
                            }
                        ],
                    },
                },
                "sample_data": "",
                "datasource": "s3-firehose",
            }
        f = DataSetWebClient().post_dataset_bucket(payload=payload)
        print(f.text)
    return {}
