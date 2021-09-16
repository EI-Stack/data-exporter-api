from flask import Blueprint, request, current_app
import requests
import json

spc_bp = Blueprint("spc_bp", __name__)

headers = {"X-Ifp-App-Secret": "OWFhYThkZWEtOGFjZS0xMWViLTk4MzItMTZmODFiNTM3OTI4"}

query_with_date = """
    query parameter($id: ID!, $from: DateTime!, $to: DateTime!) {
    parameter(id: $id){
            id
            _id
    valuesInRange(from: $from to: $to){
      num
    }
  }
}
"""
query_with_limit = """
    query parameter($id: ID! $n: Int!) {
    parameter(id: $id){
            id
            _id
    limitToNthValues(n: $n){
      num
    }
  }
}
"""
variables = {
    "id": "",
}


@spc_bp.route("/data/<parameter_id>", methods=["GET"])
def get_data_with_date(parameter_id):
    if not parameter_id:
        raise ValueError("Can not Find parameter_id")
    variables.update({"id": parameter_id})
    start = request.args.get("StartTime", "")
    end = request.args.get("EndTime", "")
    if (not start) or (not end):
        raise ValueError(
            "Must fill start and end datetime. Example: 2021-07-03T04:01:53.835Z"
        )
    variables.update({"from": start, "to": end})
    try:
        r = requests.post(
            current_app.config["EKS_URL"],
            json={"query": query_with_date, "variables": variables},
            headers=headers,
        )
    except Exception as e:
        raise e
    result = json.loads(r.text)
    values = [
        i.get("num") for i in result.get("data").get("parameter").get("valuesInRange")
    ]
    limit = request.args.get("Limit", "")
    if limit:
        values = values[: int(limit)]
    return {"data": values}
