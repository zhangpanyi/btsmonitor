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
        self.access     = data['access']
        # 账户名
        self.account    = data['account']
        # 活动key
        self.active_key = data['active_key']
        # 备注key
        self.memo_key   = data['memo_key']
        # 绑定地址
        self.rpc_host   = data['rpc_host']
        # 绑定端口
        self.rpc_port   = data['rpc_port']
        # 工人数量
        self.workernum  = data['workernum']
        # 回调地址
        self.webhook    = data['webhook']

    def get_last_op_number(self):
        ''' 获取最后操作数量
        '''
        data = yaml.load(open('lastop.yml', 'rb'))
        return data['op_number']

    def update_last_op_number(self, op_number):
        ''' 更新最后操作数量
        '''
        data = {'op_number': op_number}
        handle = open('lastop.yml', 'w')
        yaml.dump(data, handle)
        handle.close()
