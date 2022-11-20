# python3
# -*- coding: utf-8 -*-
# @Time    : 2022/8/14 13:15
# @Author  : yzyyz
# @Email   :  youzyyz1384@qq.com
# @File    : path.py
# @Software: PyCharm
from pathlib import Path

LOCAL = Path() / "陕西共青团工具"
DXX_PATH = LOCAL / "da_xue_xi"
CONFIG_PATH = LOCAL / 'config.yml'
AUTH_PATH = LOCAL / 'auth.json'
OUTPUT_PATH = LOCAL / 'output'
YOUTH_DATA_PATH = LOCAL / 'youth_data.json'
YOUTH_QQ_PATH = LOCAL / 'youth_qq.json'
IMG_OUTPUT_PATH = LOCAL / 'img_output'
VERIFY_PATH = IMG_OUTPUT_PATH / "verify"
LOCK_PATH = LOCAL / 'lock.txt'
OID_PATH = LOCAL / 'oid.txt'
