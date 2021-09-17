import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta


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


def complement_csv_value(df):
    # grouper = df.groupby('time').describe()
    df["time"] = df["time"].apply(delete_seconds)
    df["time"] = df["time"].apply(set_time_interval)
    new_df = df.groupby("time").mean().reset_index()
    # --ADD other column--
    # new_df['time'] = new_df.index
    # new_df['key'] = 1
    # other_df = df[['scadaId', 'tagId']].loc[:0, ['scadaId', 'tagId']]
    # other_df['key'] = 1
    # res = new_df.reset_index().merge(other_df, on='key').drop('key', 1)
    new_df.insert(
        2, "savedAt", new_df["time"].apply(lambda d: int(datetime.timestamp(d) * 1000))
    )
    new_df["time"] = new_df["time"].apply(
        lambda d: d.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    )
    return new_df

    # --Datetime change--
    # normalized["savedAt"] = pd.to_datetime(
    #     normalized["savedAt"], format="%Y-%m-%dT%H:%M:%S.%fZ"
    # )
    # normalized["savedAt"] = normalized["savedAt"].apply(
    #     lambda d: int(datetime.timestamp(d) * 1000)
    # )
    # normalized["time"] = pd.to_datetime(
    #     normalized["time"], format="%Y-%m-%dT%H:%M:%S.%fZ"
    # )
    # normalized["time"] = normalized["time"].apply(
    #     lambda d: d.strftime("%Y/%m/%d %p %H:%M:%S")
    #     .replace("AM", "上午")
    #     .replace("PM", "下午")
    # )
