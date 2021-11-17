import logging
import os
from datetime import datetime, timedelta

from flask import current_app

from data_exporter import scheduler
from data_exporter.config import Config
from data_exporter.utils.web_client import AzureBlob

SPLIT_TIME = 15


def delete_seconds(time):
    return (datetime.strptime(time, "%Y-%m-%dT%H:%M:%S.%fZ")).replace(microsecond=0)


def set_time_interval(x):
    x_time = float(f"{x.minute}.{x.second}")
    # print(x_time, x.minute, x.second)
    if 0 <= x_time < 15:
        y = x.replace(minute=15, second=0)
    elif 15 <= x_time < 30:
        y = x.replace(minute=30, second=0)
    elif 30 <= x_time < 45:
        y = x.replace(minute=45, second=0)
    elif 45 <= x_time < 60:
        y = x.replace(minute=0, second=0)
        y = y + timedelta(hours=1)
    else:
        raise TypeError("datetime match wrong")
    return y


def complement_csv_value(df, target):
    df["time"] = df["time"].apply(delete_seconds)
    df = df.set_index("time")
    if "num" == target:
        new_df = df.num.resample(rule="15T").mean()
    else:
        new_df = df.value.resample(rule="15T").mean()
    new_df = new_df.reset_index()
    new_df.fillna(method="pad", axis=0, inplace=True)
    new_df.insert(
        2, "savedAt", new_df["time"].apply(lambda d: int(datetime.timestamp(d) * 1000))
    )
    new_df["time"] = new_df["time"].apply(
        lambda d: d.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    )
    return new_df


def complement_dataset_value(df, target):
    # df["time"] = df["logTime"].apply(delete_seconds)
    df = df.set_index("logTime")
    if "num" == target:
        new_df = df.num.resample(rule="15T").mean()
    else:
        new_df = df.value.resample(rule="15T").mean()
    new_df = new_df.reset_index()
    new_df.fillna(method="pad", axis=0, inplace=True)
    # new_df.insert(
    #     2, "savedAt", new_df["time"].apply(lambda d: int(datetime.timestamp(d) * 1000))
    # )
    new_df["logTime"] = new_df["logTime"].apply(
        lambda d: d.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    )
    return new_df


def check_data_count(normalized_df):
    if datetime.fromtimestamp(
        normalized_df.tail(1)["savedAt"] / 1000
    ) - datetime.fromtimestamp(normalized_df.head(1)["savedAt"] / 1000) < timedelta(
        days=30
    ):
        return False
    return True


def check_target(df):
    columns = df.columns
    if "num" in columns:
        target = "num"
    else:
        target = "value"
    logging.info("[TARGET_TYPE]:  " + target)
    return target


def clean_csv():
    with scheduler.app.app_context():
        now = datetime.utcnow()
        azure_blob = AzureBlob(Config.get_env_res("AZURE_STORAGE_CONNECTION"))
        generator = azure_blob.blob_service_client.get_container_client(
            current_app.config["S3_BUCKET_NAME"]
        )
        for blob in generator.list_blobs():
            if (
                now - blob.last_modified.replace(tzinfo=None) > timedelta(hours=12)
            ) and (blob.name != "ATML_BE5P1_KW.csv"):
                blob_client = azure_blob.blob_service_client.get_blob_client(
                    container=current_app.config["S3_BUCKET_NAME"], blob=blob.name
                )
                blob_client.delete_blob()
        location = "./csv_file"
        for f in os.listdir(location):
            file_name = f"{location}/{f}"
            creation_time = os.path.getctime(file_name)
            creation_time = datetime.utcfromtimestamp(creation_time)
            if now - creation_time > timedelta(hours=12):
                os.remove(file_name)
                logging.info("[DELETE_CSV_FILE]:  " + file_name)

        # dataset_web_client = DataSetWebClient()
        # res = dataset_web_client.get_dataset_information()
        # data = json.loads(res.text)
        # exist = False
        # dataset_id = ""
        # for item in data.get("resources"):
        #     if item.get("name") == data_set_name:
        #         dataset_id = item.get("uuid")
        #         f = dataset_web_client.get_dataset_config(item.get("uuid"))
        #         payload = json.loads(f.text)
        #         if not payload.get("firehose").get("data").get("containers"):
        #             return (
        #                 jsonify(
        #                     {"message": "Wrong bucket is about 'Blob'"},
        #                 ),
        #                 404,
        #             )
        #         for data in payload.get("firehose").get("data").get("containers"):
        #             if data.get("container") == blob_bucket_name:
        #                 files = data.get("blobs").get("files")
        #                 files.append(f"{file_name}.csv")
        #         # put file
        #         dataset_web_client.put_dataset_config(
        #             dataset_uuid=item.get("uuid"), payload=payload
        #         )
        #         exist = True
        #         break
        # if not exist:
        #     dataset_id = set_blob_dataset(data_set_name, file_name, blob_bucket_name)




        # MinIO csv files
        # dataset_web_client = DataSetWebClient()
        # client = dataset_web_client.get_minio_client(
        #     current_app.config["S3_BUCKET_NAME"]
        # )
        # objects_to_delete = client.list_objects(
        #     current_app.config["S3_BUCKET_NAME"], recursive=True
        # )
        # if objects_to_delete:
        #     for obj in objects_to_delete:
        #         if now - obj.last_modified.replace(tzinfo=None) > timedelta(hours=12):
        #             client.remove_object(current_app.config["S3_BUCKET_NAME"], obj.object_name)
        # local csv files
