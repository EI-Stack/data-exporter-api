from datetime import datetime

from flask import Blueprint, request
import json

from data_exporter.utils.parameter_helper import transfer_to_big_parameter_id
from data_exporter.utils.web_client import DataSetWebClient

spc_bp = Blueprint("spc_bp", __name__)

headers = {"X-Ifp-App-Secret": "OWFhYThkZWEtOGFjZS0xMWViLTk4MzItMTZmODFiNTM3OTI4"}


@spc_bp.route("/spc/date/<parameter_id>", methods=["GET"])
def get_data_with_date(parameter_id):
    if not parameter_id:
        raise ValueError("Can not Find parameter_id")
    parameter_id = transfer_to_big_parameter_id(parameter_id)
    start = request.args.get("start_time", "")
    end = request.args.get("end_time", "")
    if (not start) or (not end):
        raise ValueError(
            "Must fill start and end datetime. Example: 2021-07-03T04:01:53.835Z"
        )
    variables = {"id": parameter_id, "from": start, "to": end}
    r = DataSetWebClient.get_dataset_with_graphql_by_date(variables)
    result = json.loads(r.text)
    if not result.get("data").get("parameter"):
        return {"data": []}
    values = [
        i.get("num") for i in result.get("data").get("parameter").get("valuesInRange")
    ]
    return {"data": values}


@spc_bp.route("/spc/limit/<parameter_id>", methods=["GET"])
def get_data_with_limit(parameter_id):
    if not parameter_id:
        raise ValueError("Can not Find parameter_id")
    parameter_id = transfer_to_big_parameter_id(parameter_id)
    limit = request.args.get("limit", 10)
    if not limit:
        raise ValueError("Must fill limit count.")
    variables = {"id": parameter_id, "n": int(limit)}
    r = DataSetWebClient.get_dataset_with_graphql_by_limit(variables)

    result = json.loads(r.text)
    if not result.get("data").get("parameter"):
        return {"data": []}
    values = [
        i.get("num")
        for i in result.get("data").get("parameter").get("limitToNthValues")
    ]
    return {"data": values}
