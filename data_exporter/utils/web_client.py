import requests
import json
from minio import Minio
from flask import current_app

URL = current_app.config['AFS_URL']
INSTANCE_ID = '2174f980-0fc1-5b88-913b-2db9c1deccc5'
HEADERS = {"X-Ifp-App-Secret": "OWFhYThkZWEtOGFjZS0xMWViLTk4MzItMTZmODFiNTM3OTI4"}
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
body = {"username": "she30338@gmail.com", "password": "Jk840118!"}
S3_bucket_name = "test-grant"


def get_token():
    r = requests.post(
        f"http://api-sso-ensaas.sa.wise-paas.com/v4.0/auth/native", json=body
    )
    result = json.loads(r.text)
    token = result.get("tokenType") + " " + result.get("accessToken")
    return token


class DataSetWebClient:

    def __init__(self):
        self.headers = {"Authorization": get_token(), "accept": "application/json", "content-type": "application/json"}

    @staticmethod
    def get_minio_client():
        print(current_app.config['S3_ENDPOINT'])
        client = Minio(
            current_app.config['S3_ENDPOINT'],
            access_key=current_app.config['S3_ACCESS_KEY'],
            secret_key=current_app.config['S3_SECRET_KEY'],
        )
        # print(client.list_buckets())
        found = client.bucket_exists(S3_bucket_name)
        if not found:
            client.make_bucket(S3_bucket_name)
        else:
            print(f"Bucket '{S3_bucket_name}' already exists")
        return client

    @staticmethod
    def get_dataset_with_graphql(variables):
        try:
            r = requests.post(
                current_app.config["EKS_URL"],
                json={"query": query_with_limit, "variables": variables},
                headers=HEADERS,
            )
        except Exception as e:
            raise e
        return r

    def get_dataset_information(self):
        try:
            r = requests.get(f"{URL}/v2/instances/{INSTANCE_ID}/datasets", headers=self.headers)
        except Exception as e:
            raise e
        return r

    def get_dataset_config(self, dataset_uuid):
        try:
            r = requests.get(
                f"{URL}/v2/instances/{INSTANCE_ID}/datasets/{dataset_uuid}",
                headers=self.headers
            )
        except Exception as e:
            raise e
        return r

    def put_dataset_config(self, dataset_uuid, payload):
        try:
            r = requests.put(
                f"{URL}/v2/instances/{INSTANCE_ID}/datasets/{dataset_uuid}",
                json=payload,
                headers=self.headers
            )
        except Exception as e:
            raise e
        return r

    def post_dataset_bucket(self, payload):
        try:
            r = requests.post(
                f"{URL}/v2/instances/{INSTANCE_ID}/datasets",
                json=payload,
                headers=self.headers
            )
        except Exception as e:
            raise e
        return r


