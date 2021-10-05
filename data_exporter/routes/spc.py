import json
from datetime import datetime, timedelta

import pandas as pd
from flask import Blueprint, request

from data_exporter.models import SpcData
from data_exporter.models.ensaas import MongoDB
from data_exporter.utils.csv_value_helper import complement_csv_value, check_target
from data_exporter.utils.dataset_helper import (
    transfer_to_big_parameter_id,
    split_datetime,
    concat_split_datetime_dataset,
)

spc_bp = Blueprint("spc_bp", __name__)

headers = {"X-Ifp-App-Secret": "OWFhYThkZWEtOGFjZS0xMWViLTk4MzItMTZmODFiNTM3OTI4"}


@spc_bp.route("/spc/date/<parameter_id>", methods=["GET"])
def get_data_with_date(parameter_id):
    if not parameter_id:
        raise ValueError("Can not Find parameter_id")
    # parameter_id = transfer_to_big_parameter_id(parameter_id)
    start = request.args.get("start_time", "")
    end = request.args.get("end_time", "")
    if (not start) or (not end):
        raise ValueError(
            "Must fill start and end datetime. Example: 2021-07-03T04:01:53.835Z"
        )
    start = datetime.strptime(start, "%Y-%m-%dT%H:%M:%S.%fZ")
    end = datetime.strptime(end, "%Y-%m-%dT%H:%M:%S.%fZ")
    date_list = split_datetime(start, end)
    normalized_all = concat_split_datetime_dataset(date_list, parameter_id)
    if normalized_all.empty:
        return {"data": []}
    target = check_target(normalized_all)
    df_num = normalized_all[target]
    df_num = df_num.to_dict()
    values = [value for _, value in df_num.items()]
    return {"data": values}


@spc_bp.route("/spc/limit/<parameter_id>", methods=["GET"])
def get_data_with_limit(parameter_id):
    if not parameter_id:
        raise ValueError("Can not Find parameter_id")
    # parameter_id = transfer_to_big_parameter_id(parameter_id)
    limit = request.args.get("limit", 10)
    if not limit:
        raise ValueError("Must fill limit count.")
    mongo = MongoDB()
    df_all = pd.DataFrame()
    collection_list = ["ifp.core.kw_real_time", "ifp.core.kwh_real_time"]
    for collection in collection_list:
        mongo_db = mongo.DATABASE[collection]
        cursor = mongo_db.find({"parameterNodeId": parameter_id})
        df = pd.DataFrame(list(cursor))
        df_all = pd.concat([df_all, df], ignore_index=True)
    if df_all.empty:
        return {"data": []}
    target = check_target(df_all)
    df_num = df_all[target]
    df_num = df_num.to_dict()
    values_list = [value for _, value in df_num.items()]
    values = values_list[-int(limit) :]
    # print(df_all[['logTime', 'parameterNodeId', 'value']])
    # data = SpcData.objects(ParameterID=parameter_id).order_by("-created_at").first()
    # if not data:
    #     return {"data": []}
    # value_list = json.loads(data.value_list)
    # values = value_list[-int(limit) :]
    return {"data": values}
