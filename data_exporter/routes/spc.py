from datetime import datetime, timedelta

import pandas as pd
from flask import Blueprint, request, jsonify, current_app
from pymongo import ASCENDING, DESCENDING

from data_exporter.utils.csv_value_helper import complement_csv_value, check_target
from data_exporter.utils.dataset_helper import (
    transfer_to_big_parameter_id,
    split_datetime,
    concat_split_datetime_dataset,
)
from data_exporter.utils.web_client import EnsaasMongoDB

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
    limit = int(request.args.get("limit", 10))
    if not limit:
        raise ValueError("Must fill limit count.")
    mongo = EnsaasMongoDB()
    mongo_db = mongo.DATABASE["iii.pml.task"]
    df_all = pd.DataFrame()
    if mongo_db:
        cursor = mongo_db.find({"ParameterID": parameter_id})
        data = list(cursor)
        # print(list(cursor)[0].get('UsageType'))
        if not data:
            return (
                jsonify(
                    {"message": "Data is not enough"},
                ),
                404,
            )
        if data[0].get('UsageType') == 'EnergyDemand':
            collection = "ifp.core.kw_real_time"
        else:
            collection = "ifp.core.kwh_real_time"
        mongo_db = mongo.DATABASE[collection]
        cursor = mongo_db.find({"parameterNodeId": parameter_id}).sort([('logTime', DESCENDING)]).limit(limit)
        df_all = pd.DataFrame(list(cursor))
    else:
        for collection in ["ifp.core.kw_real_time", "ifp.core.kwh_real_time"]:
            mongo_db = mongo.DATABASE[collection]
            cursor = mongo_db.find({"parameterNodeId": parameter_id}).sort([('logTime', DESCENDING)]).limit(limit)
            df = pd.DataFrame(list(cursor))
            df_all = pd.concat([df_all, df], ignore_index=True)
    if df_all.empty:
        return (
            jsonify(
                {"message": "Data is not enough"},
            ),
            404,
        )
    match_key = ['deviceKindUsage', 'energyDeviceKind', 'machineNodeId']
    df_key = df_all.groupby(match_key)
    res_key = [i[0]for i in df_key][0]
    res_dict = dict(zip(match_key, res_key))
    # df_all = df_all.set_index("logTime")
    target = check_target(df_all)
    # if "num" == target:
    #     new_df = df_all.num.resample(rule="15T").mean().ffill()
    # else:
    #     new_df = df_all.value.resample(rule="15T").mean().ffill()
    # new_df = new_df.reset_index()
    df_num = df_all[target]
    df_num = df_num.to_dict()
    values_list = [value for _, value in df_num.items()]
    # values = values_list[-int(limit):]
    values_list.reverse()
    if len(values_list) != int(limit):
        return (
            jsonify(
                {"message": "Data is not enough"},
            ),
            404,
        )
    res_dict.update({"data": values_list})
    return res_dict
