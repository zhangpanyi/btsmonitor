# -*- coding:utf-8 -*-

import os
import logging
from logging.handlers import RotatingFileHandler

def init_logger():
    ''' 初始日志
    '''
    # 日志格式
    fmt = '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s'
    formatter = logging.Formatter(fmt)

    # 终端输出
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    console.setLevel(logging.INFO)
    logging.getLogger().addHandler(console)

    # 文件输出
    logpath = 'logs/log.txt'
    dir, _ = os.path.split(logpath)
    os.makedirs(dir, exist_ok=True)
    handler = RotatingFileHandler(logpath, maxBytes=10*1024*1024, backupCount=100)
    handler.setLevel(logging.INFO)
    handler.setFormatter(formatter)

    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.NOTSET)

init_logger()
