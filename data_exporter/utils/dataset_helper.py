import base64
import json
import logging
from datetime import datetime, timedelta
from uuid import uuid4
import pandas as pd
from flask import current_app

from data_exporter import scheduler
from data_exporter.models.ensaas import MongoDB
from data_exporter.utils.csv_value_helper import check_target, complement_csv_value
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
    if end - start < timedelta(days=30):
        return [
            [
                start.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                end.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            ]
        ]
    n = 5
    diff = (end - start) // (n - 1)
    for idx in range(0, n):
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


def get_normalized_all(variables):
    r = DataSetWebClient().get_dataset_with_graphql_by_date(variables)
    data = pd.read_json(r.text)["data"]["parameter"]
    normalized = pd.json_normalize(data, "valuesInRange", ["scadaId", "tagId"])
    return normalized


def concat_split_datetime_dataset(date_list, parameter_id):
    normalized_all = pd.DataFrame()
    for i, date in enumerate(date_list):
        variables = {"id": parameter_id, "from": date[0], "to": date[1]}
        normalized = get_normalized_all(variables)
        # print(normalized)
        normalized_all = pd.concat([normalized_all, normalized], ignore_index=True)
    return normalized_all


def spc_routine():
    with scheduler.app.app_context():
        ensaas = MongoDB()
        ensaas_db = ensaas.DATABASE["iii.pml.task"]
        if not ensaas_db:
            raise logging.info(ensaas_db)
        parameter_id_list = ensaas_db.distinct("ParameterID")
        if not parameter_id_list:
            return
        spc_data_list = []
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=100)
        date_list = split_datetime(start_time, end_time)
        from data_exporter.models import SpcData

        for parameter_id in parameter_id_list:
            logging.info("[PARAMETER_ID]: " + parameter_id)
            normalized_all = concat_split_datetime_dataset(date_list, parameter_id)
            if normalized_all.empty:
                continue
            target = check_target(normalized_all)
            normalized = complement_csv_value(normalized_all, target)
            df_num = normalized[target]
            df_num = df_num.to_dict()
            values = [value for _, value in df_num.items()]
            values_list = json.dumps(values)
            spc_data_list.append(
                SpcData(
                    **{
                        "uuid": str(uuid4()),
                        "ParameterID": parameter_id,
                        "value_list": values_list,
                    }
                )
            )
            logging.info("[END QUERY]: " + parameter_id)
        logging.info("[INSERT PARAMETER INFO]: " + parameter_id)
        SpcData.objects.insert(spc_data_list)
