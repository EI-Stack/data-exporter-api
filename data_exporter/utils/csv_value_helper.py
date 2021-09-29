import logging
from datetime import datetime, timedelta

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
    logging.info("target:  " + target)
    return target
