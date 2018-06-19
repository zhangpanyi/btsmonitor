# -*- coding:utf-8 -*-

import os
from .singleton import Singleton

CONFIG_FILE_PATH = 'server.yml'

@Singleton
class SysConfig(object):
    ''' 系统配置
    '''
    def __init__(self):
        # 接入点
        self.wss = 'wss://ws.gdex.top'
        # 账户名
        self.account = 'bts'
        # 绑定地址
        self.rpc_host = '127.0.0.1'
        # 绑定端口
        self.rpc_port = 18080
        # 用户名
        self.username = None
        # 密码
        self.password = None
        # 工人数量
        self.workernum = 10
        # 回调地址
        self.webhook = None
        self._init_from_file()

    def _init_from_file(self):
        ''' 从配置文件初始化
        '''
        pass
