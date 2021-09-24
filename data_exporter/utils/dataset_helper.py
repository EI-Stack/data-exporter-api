import base64
import json
import threading

import pandas as pd
from flask import current_app

from data_exporter.utils.web_client import DataSetWebClient
import multiprocessing


def transfer_to_big_parameter_id(parameter_id):
    # desk parameter_id 轉 parameterID 方法
    object_id = parameter_id
    model_name = "Parameter"
    model_name = bytes(model_name, "utf-8")
    model_name = bytes.decode(base64.urlsafe_b64encode(model_name))
    object_id = bytes.fromhex(object_id)
    object_id = bytes.decode(base64.urlsafe_b64encode(object_id))
    node_id = model_name + "." + object_id
    return node_id


def split_list(l, n):
    # 將list分割 (l:list, n:每個matrix裡面有n個元素)
    for idx in range(0, len(l)):
        if idx + n > len(l):
            continue
        yield l[idx : idx + n]


def split_datetime(start, end):
    temp = []
    N = 25
    diff = (end - start) // (N - 1)
    for idx in range(0, N):
        # computing new dates
        temp.append((start + idx * diff).strftime("%Y-%m-%dT%H:%M:%S.%fZ"))
    result = list(split_list(temp, 2))
    return result


def set_s3_dataset(data_set_name, file_name, s3_bucket_name):
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
                        "bucket": s3_bucket_name,
                    }
                ],
            },
        },
        "sample_data": "",
        "datasource": "s3-firehose",
    }
    r = DataSetWebClient().post_dataset_bucket(payload=payload)
    dataset_id = json.loads(r.text).get("uuid")
    return dataset_id


def get_normalized_all(variables, return_list, app):
    with app.app_context():
        r = DataSetWebClient().get_dataset_with_graphql_by_date(variables)
        data = pd.read_json(r.text)["data"]["parameter"]
        normalized = pd.json_normalize(data, "valuesInRange", ["scadaId", "tagId"])
        return_list.append(normalized)
    # normalized_all = pd.concat(
    #     [normalized_all, normalized], axis=0, ignore_index=True
    # )


def concat_split_datetime_dataset(date_list, parameter_id):
    # normalized_all = pd.DataFrame()
    jobs = []
    return_list = []
    app = current_app._get_current_object()
    for i, date in enumerate(date_list):
        variables = {"id": parameter_id, "from": date[0], "to": date[1]}
        p = threading.Thread(
            target=get_normalized_all, args=(variables, return_list, app)
        )
        print(p)
        jobs.append(p)
        jobs[i].start()
    for t in jobs:
        t.join()
    normalized_all = pd.concat(return_list, ignore_index=True)
    return normalized_all
