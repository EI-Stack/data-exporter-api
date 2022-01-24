import time
import os
import requests
import json
from minio import Minio
from flask import current_app
from azure.storage.blob import BlobServiceClient, __version__, BlobServiceClient
from mongo_proxy import MongoProxy
from pymongo import MongoClient

from data_exporter.config import Config

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
            "Authorization": Config.get_env_res("Authorization"),
            "accept": "application/json",
            "content-type": "application/json",
        }
        self.afs_url = Config.get_env_res("AFS_API_URL")
        self.eks_url = current_app.config["IFP_DESK_API_URL"]
        self.instance_id = Config.get_env_res("AFS_INSTANCES_ID")
        self.ifp_headers = {current_app.config["IFP_DESK_CLIENT_SECRET"]}

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
                f"{self.afs_url}/instances/{self.instance_id}/datasets",
                headers=self.token_headers,
            )
        except Exception as e:
            raise e
        return r

    def get_dataset_config(self, dataset_uuid):
        try:
            r = requests.get(
                f"{self.afs_url}/instances/{self.instance_id}/datasets/{dataset_uuid}",
                headers=self.token_headers,
            )
        except Exception as e:
            raise e
        return r

    def put_dataset_config(self, dataset_uuid, payload):
        try:
            r = requests.put(
                f"{self.afs_url}/instances/{self.instance_id}/datasets/{dataset_uuid}",
                json=payload,
                headers=self.token_headers,
            )
        except Exception as e:
            raise e
        return r

    def post_dataset_bucket(self, payload):
        try:
            r = requests.post(
                f"{self.afs_url}/instances/{self.instance_id}/datasets",
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


class AzureBlob:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, AZURE_STORAGE_CONNECTION):
        print("[___________________________ CONNECT AZUREBLOB ___________________________]")
        try:
            print("Azure Blob Storage v" + __version__ + " - connect success .")
            print(AZURE_STORAGE_CONNECTION)
            self.blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION)
        except Exception as e:
            print('Exception:', e)

    def ListContainer(self):
        containerArray = []
        container_list = self.blob_service_client.list_containers()
        for container in container_list:
            containerArray.append(container.name)
        return (containerArray)

    def ListBlob(self, container_name):
        try:
            blobArray = []
            container_client = self.blob_service_client.get_container_client(container_name)
            blob_list = container_client.list_blobs()
            for blob in blob_list:
                blobArray.append(blob.name)
            return (blobArray)
        except Exception as e:
            return ('Exception:' + str(e))

    def CreateContainer(self, container_name):
        try:
            container_client = self.blob_service_client.create_container(container_name)
            return ('Success CreateContainer :' + container_name)
        except Exception as e:
            return ('Exception:' + str(e))

    def DeleteContainer(self, container_name):
        try:
            container_client = self.blob_service_client.delete_container(container_name)
            return ('Success DeleteContainer :' + container_name)
        except Exception as e:
            return ('Exception:' + str(e))

    def UploadFile(self, container_name, local_path, local_file_name):
        try:
            upload_file_path = os.path.join(local_path, local_file_name)
            blob_client = self.blob_service_client.get_blob_client(container=container_name, blob=local_file_name)
            with open(upload_file_path, "rb") as data:
                blob_client.upload_blob(data, max_concurrency=30, timeout=72000)
                # blob_client.upload_blob(data, max_concurrency=30, timeout=72000, blob_type='AppendBlob')
            return ('Success UploadFile: ' + local_file_name)
        except Exception as e:
            return ('Exception:' + str(e))

    def DownloadFile(self, container_name, file_name):
        try:
            blob_client = self.blob_service_client.get_blob_client(container=container_name, blob=file_name)
            with open(file_name, "wb") as my_blob:
                blob_data = blob_client.download_blob()
                blob_data.readinto(my_blob)
            return ('Success DownloadFile: ' + file_name)
        except Exception as e:
            return ('Exception:' + str(e))

    def DeleteFile(self, container_name, file_name):
        try:
            blob_client = self.blob_service_client.get_blob_client(container=container_name, blob=file_name)
            blob_client.delete_blob()
            return ('Success DeleteFile: ' + file_name)
        except Exception as e:
            return ('Exception:' + str(e))

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
