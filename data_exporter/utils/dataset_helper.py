import base64
import json

import pandas as pd

from data_exporter.utils.web_client import DataSetWebClient


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
    N = 30
    diff = (end - start) // (N - 1)
    for idx in range(0, N):
        # computing new dates
        temp.append((start + idx * diff).strftime("%Y-%m-%dT%H:%M:%S.%fZ"))
    result = list(split_list(temp, 2))
    return result


def set_s3_dataset(current_app, data_set_name, file_name, s3_bucket_name):
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


def concat_split_datetime_dataset(date_list, parameter_id):
    normalized_all = pd.DataFrame()
    for i, date in enumerate(date_list):
        variables = {"id": parameter_id, "from": date[0], "to": date[1]}
        r = DataSetWebClient.get_dataset_with_graphql_by_date(variables)
        data = pd.read_json(r.text)["data"]["parameter"]
        normalized = pd.json_normalize(data, "valuesInRange", ["scadaId", "tagId"])
        print(normalized.index, date[0], date[1])
        normalized_all = pd.concat(
            [normalized_all, normalized], axis=0, ignore_index=True
        )
    return normalized_all
