# -*- coding:utf-8 -*- 

import asyncio
from . import asyncrpc, asyncws

def id_to_int(id):
    return int(id.split('.')[-1])

class Statistics(asyncws.AsyncWs):
    """ 账户信息统计模块
        :param url 节点地址
        :param account 账户名称
    """
    last_trx = ''
    node_api = None
    last_op = '2.9.1'
    account = {'name': '', 'id': '', 'statistics': ''}

    def __init__(self, url, account, num_workers=10):
        super(Statistics, self).__init__(url, num_workers=num_workers)
        self._statistics = None
        self.account["name"] = account
        self.node_api = asyncrpc.AsyncRPC(url)

    def future_list(self):
        """ 任务列表
        """
        futures = super(Statistics, self).future_list()
        return futures + self.node_api.future_list()

    async def on_statistics(self, notify):
        """ 帐户更新
        """
        trx_last = self.last_trx
        trx_current = notify['most_recent_op']
        if id_to_int(trx_current) > id_to_int(trx_last):
            self.last_trx = trx_current
        else:
            return

        while True:
            if id_to_int(trx_current) <= id_to_int(trx_last):
                return
            trx_info = (await self.node_api.get_objects([trx_current]))[0]
            if id_to_int(trx_info['operation_id']) <= id_to_int(self.last_op):
                return

            await self.process_operations(trx_info['operation_id'])
            trx_current = trx_info['next']

    async def process_operations(self, op_id):
        """ 处理操作
        """
        pass

    async def _on_open(self):
        """ 连接成功
        """
        await super(Statistics, self)._on_open()

        # 获取账户信息
        response = await self.rpc(
            [self.database_api, 'get_account_by_name', [self.account['name']]])
        self.account['id'] = response['id']
        self.account['statistics'] = response['statistics']

        # 订阅账户更新
        statistics = await self.rpc([self.database_api, 'get_objects', [[self.account['statistics']]]])
        statistics_info = statistics[0]
        if self.last_trx == '':
             self.last_trx = statistics_info['most_recent_op']
        await self.on_statistics(statistics_info)
        self.subscribe(self.account['statistics'], self.on_statistics)
