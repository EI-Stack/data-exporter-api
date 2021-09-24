from uuid import uuid4
from datetime import datetime
from data_exporter.models import Waconn, Wadata, Wacfg


def get_datetime_strptime(ts):
    return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S.%fZ")


class MqttTopicHandler:
    def __init__(self, res_dict):
        self.ts = get_datetime_strptime(res_dict.get("ts"))
        self.res_dict = res_dict

    def waconn_info(self):
        info_dict = self.res_dict.get("d", {})
        if (not info_dict) or (not info_dict.get("ifp")):
            return
        ifp = info_dict.get("ifp")
        print("-------waconn-------")
        print("val     :", ifp)
        waconn_list = []
        for i, waconn_list in ifp.items():
            waconn_list.append(
                Waconn(**{"uuid": str(uuid4()), "type": i, "status": j, "ts": self.ts})
            )
        Waconn.objects.insert(waconn_list)

    def wadata_info(self):
        info_dict = self.res_dict.get("d", {})
        if (not info_dict) or (not info_dict.get("ifp")):
            return
        ifp = info_dict.get("ifp")
        val = ifp.get("Val")
        if not val:
            return
        print("-------wadata-------")
        print("val     :", val)
        wadata_list = []
        for i, j in val.items():
            wadata_list.append(
                Wadata(
                    **{
                        "uuid": str(uuid4()),
                        "tag_id": i,
                        "value": j,
                        "ts": self.ts,
                    }
                )
            )
        Wadata.objects.insert(wadata_list)

    def wacfg_info(self):
        info_dict = self.res_dict.get("d", {})
        if (not info_dict) or (not info_dict.get("ifp")):
            return
        ifp = info_dict.get("ifp")
        print("-------wacfg-------")
        print("val     :", ifp)
        wacfg_list = []
        for i, j in ifp.items():
            for m, n in j.items():
                device_type = n.get("TID")
                wacfg_list.append(
                    Wacfg(
                        **{
                            "uuid": str(uuid4()),
                            "tag_status": i,
                            "tag_id": m,
                            "device_type": device_type,
                            "ts": self.ts,
                        }
                    )
                )
        Wacfg.objects.insert(wacfg_list)

    # def ifpcfg_info(self):
    #     info_dict = self.res_dict.get("d", {})
    #     if (not info_dict) or (not info_dict.get("ifp")):
    #         return
    #     group = info_dict.get("group")
    #     pass
