import requests
import json
from minio import Minio
from flask import current_app
from concurrent.futures import ThreadPoolExecutor, wait

# 拆 os env
URL = current_app.config["AFS_URL"]
INSTANCE_ID = "2174f980-0fc1-5b88-913b-2db9c1deccc5"
HEADERS = {"X-Ifp-App-Secret": "OWFhYThkZWEtOGFjZS0xMWViLTk4MzItMTZmODFiNTM3OTI4"}
query_with_date = """
    query parameter($id: ID! $from: DateTime!, $to: DateTime!) {
    parameter(id: $id){
            id
            _id
            scadaId
            tagId
    valuesInRange(from: $from to: $to){
      time
      num
      savedAt
    }
  }
}
"""
query_with_limit = """
    query parameter($id: ID! $n: Int!) {
    parameter(id: $id){
            id
            _id
            scadaId
            tagId
    limitToNthValues(n: $n){
      time
      num
      savedAt
    }
  }
}
"""


#  網址拆os env
def get_sso_token():
    r = requests.get(
        "https://ifps-predict-train-ifpsdev-eks005.sa.wise-paas.com/api/v1/token"
    )
    result = json.loads(r.text)
    token = result.get("Authorization")
    return token


#  類別拆開 singleturn
class DataSetWebClient:
    def __init__(self):
        self.headers = {
            "Authorization": get_sso_token(),
            "accept": "application/json",
            "content-type": "application/json",
        }

    @staticmethod
    def get_minio_client(bucket_name):
        try:
            client = Minio(
                current_app.config["S3_ENDPOINT"],
                access_key=current_app.config["S3_ACCESS_KEY"],
                secret_key=current_app.config["S3_SECRET_KEY"],
            )
        except Exception as e:
            raise ValueError("client minio", e)
        found = client.bucket_exists(bucket_name)
        if not found:
            client.make_bucket(bucket_name)
        else:
            print(f"Bucket '{bucket_name}' already exists")
        return client

    @staticmethod
    def get_dataset_with_graphql_by_limit(variables):
        try:
            r = requests.post(
                current_app.config["EKS_URL"],
                json={"query": query_with_limit, "variables": variables},
                headers=HEADERS,
            )
        except Exception as e:
            raise e
        return r

    @staticmethod
    def get_dataset_with_graphql_by_date(variables):
        try:
            r = requests.post(
                current_app.config["EKS_URL"],
                json={"query": query_with_date, "variables": variables},
                headers=HEADERS,
            )
        except Exception as e:
            raise e
        return r

    def get_dataset_information(self):
        try:
            r = requests.get(
                f"{URL}/v2/instances/{INSTANCE_ID}/datasets", headers=self.headers
            )
        except Exception as e:
            raise e
        return r

    def get_dataset_config(self, dataset_uuid):
        try:
            r = requests.get(
                f"{URL}/v2/instances/{INSTANCE_ID}/datasets/{dataset_uuid}",
                headers=self.headers,
            )
        except Exception as e:
            raise e
        return r

    def put_dataset_config(self, dataset_uuid, payload):
        try:
            r = requests.put(
                f"{URL}/v2/instances/{INSTANCE_ID}/datasets/{dataset_uuid}",
                json=payload,
                headers=self.headers,
            )
        except Exception as e:
            raise e
        return r

    def post_dataset_bucket(self, payload):
        try:
            r = requests.post(
                f"{URL}/v2/instances/{INSTANCE_ID}/datasets",
                json=payload,
                headers=self.headers,
            )
        except Exception as e:
            raise e
        return r
