import time

import requests
import json
from minio import Minio
from flask import current_app

from mongo_proxy import MongoProxy
from pymongo import MongoClient

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


#  類別拆開 singleturn
class DataSetWebClient:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.token_headers = {
            "Authorization": current_app.config["SSO_TOKEN"],
            "accept": "application/json",
            "content-type": "application/json",
        }
        self.afs_url = current_app.config["AFS_URL"]
        self.eks_url = current_app.config["IFP_DESK_API_URL"]
        self.instance_id = current_app.config["INSTANCE_ID"]
        self.ifp_headers = {
            "X-Ifp-App-Secret": current_app.config["IFP_DESK_CLIENT_SECRET"]
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

    def get_dataset_with_graphql_by_limit(self, variables):
        try:
            r = requests.post(
                self.eks_url,
                json={"query": query_with_limit, "variables": variables},
                headers=self.ifp_headers,
            )
        except Exception as e:
            raise e
        return r

    def get_dataset_with_graphql_by_date(self, variables):
        try:
            r = requests.post(
                self.eks_url,
                json={"query": query_with_date, "variables": variables},
                headers=self.ifp_headers,
            )
        except Exception as e:
            raise e
        return r

    def get_dataset_information(self):
        try:
            r = requests.get(
                f"{self.afs_url}/v2/instances/{self.instance_id}/datasets",
                headers=self.token_headers,
            )
        except Exception as e:
            raise e
        return r

    def get_dataset_config(self, dataset_uuid):
        try:
            r = requests.get(
                f"{self.afs_url}/v2/instances/{self.instance_id}/datasets/{dataset_uuid}",
                headers=self.token_headers,
            )
        except Exception as e:
            raise e
        return r

    def put_dataset_config(self, dataset_uuid, payload):
        try:
            r = requests.put(
                f"{self.afs_url}/v2/instances/{self.instance_id}/datasets/{dataset_uuid}",
                json=payload,
                headers=self.token_headers,
            )
        except Exception as e:
            raise e
        return r

    def post_dataset_bucket(self, payload):
        try:
            r = requests.post(
                f"{self.afs_url}/v2/instances/{self.instance_id}/datasets",
                json=payload,
                headers=self.token_headers,
            )
        except Exception as e:
            raise e
        return r


class EnsaasMongoDB:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        mongoClient = MongoProxy(
            MongoClient(
                current_app.config["MONGODB_URL"],
                username=current_app.config["MONGODB_USERNAME"],
                password=current_app.config["MONGODB_PASSWORD"],
                authSource=current_app.config["MONGODB_AUTH_SOURCE"],
                authMechanism="SCRAM-SHA-1",
            )
        )
        self.DATABASE = mongoClient[current_app.config["MONGODB_DATABASE"]]


# class EKS009MongoDB:
#     def __init__(self):
#         mongoClient = MongoProxy(
#             MongoClient(
#                 current_app.config["EKS_009_HOST"],
#                 username=current_app.config["EKS_009_USERNAME"],
#                 password=current_app.config["EKS_009_PASSWORD"],
#                 authSource=current_app.config["EKS_009_DATABASE"],
#                 # authMechanism="SCRAM-SHA-1",
#             )
#         )
#         self.DATABASE = mongoClient[current_app.config["EKS_009_DATABASE"]]
