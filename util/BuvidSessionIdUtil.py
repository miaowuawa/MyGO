import random
import uuid
import hashlib


# sessionId生成方案
def genSessionId():
    session_id = "".join([hex(item)[2:] for item in random.randbytes(4)])
    return session_id


# mac地址生成方案
def create_random_mac(sep=":"):
    # 00:90:4C:11:22:33
    data_list = []
    for i in range(1, 7):
        part = "".join(random.sample("0123456789ABCDEF", 2))
        data_list.append(part)
    mac = sep.join(data_list)
    return mac


# Bvuid生成
def get_buvid_by_wifi_mac():
    mac = create_random_mac()
    md5 = hashlib.md5()
    md5.update(mac.encode('utf-8'))
    v0_1 = md5.hexdigest()
    return "XY{}{}{}{}".format(v0_1[2], v0_1[12], v0_1[22], v0_1).upper()
