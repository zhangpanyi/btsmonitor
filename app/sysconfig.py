# -*- coding:utf-8 -*-

import os
import yaml
from .singleton import Singleton

CONFIG_FILE_PATH = 'server.yml'

@Singleton
class SysConfig(object):
    ''' 系统配置
    '''
    def __init__(self):
        data = yaml.load(open(CONFIG_FILE_PATH, 'rb'))
        # 接入点
        self.wss        = data['wss']
        # 账户名
        self.account    = data['account']
        # 绑定地址
        self.rpc_host   = data['rpc_host']
        # 绑定端口
        self.rpc_port   = data['rpc_port']
        # 用户名
        self.username   = data['username']
        # 密码
        self.password   = data['password']
        # 工人数量
        self.workernum  = data['workernum']
        # 回调地址
        self.webhook    = data[ 'webhook']
