from flask import Blueprint, request, current_app
from data_exporter import mqtt
from data_exporter.utils.mqtt_topic import MqttTopicHandler
import json
print(mqtt.broker_url)
dataset_bp = Blueprint('dataset_bp', __name__)


@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    # mqtt.subscribe('iot-2/evt/waconn/fmt/grant-test')
    mqtt.subscribe('iot-2/evt/wadata/fmt/grant-test')
    mqtt.subscribe('iot-2/evt/wacfg/fmt/grant-test')
    print(mqtt.topics)


@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    payload = message.payload.decode()
    res_dict = json.loads(payload)
    print("-------msg-------")
    print('dict  :', res_dict, '<<<>>>', 'topic  :', message.topic)
    topic_type = message.topic.split('/')[2]
    if topic_type == 'waconn':
        MqttTopicHandler(res_dict).waconn_info()
    elif topic_type == 'wadata':
        MqttTopicHandler(res_dict).wadata_info()
    elif topic_type == 'wacfg':
        MqttTopicHandler(res_dict).wacfg_info()
    # elif topic_type == 'ifpcfg':
    #     MqttTopicHandler(res_dict).ifpcfg_info()


mqtt.client.on_connect = handle_connect
mqtt.client.on_message = handle_mqtt_message
print('mqtt_set')
# mqtt.client.loop_forever()
# mqtt.client.loop()


# @dataset_bp.route("/dataset/<parameter_id>", methods=["GET"])
# def get_dataset_file(parameter_id):
#
#
