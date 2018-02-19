# -*- coding:utf-8 -*- 

import asyncio
import logging
from . import statistics
from bitsharesbase import memo as BtsMemo
from bitsharesbase.account import PublicKey, PrivateKey

def id_to_int(id):
    return int(id.split('.')[-1])

class Transfer(statistics.Statistics):
    """ 账户转账模块
        :param url 节点地址
        :param account 账户名称
        :param wifkey 账户私钥
    """
    wifkey = ''
    asset_info = {}

    def __init__(self, url, account, wifkey, num_workers=10):
        super(Transfer, self).__init__(url, account, num_workers=num_workers)
        self.wifkey = wifkey

    async def on_sent(self, trx):
        """ 发送资产
        """
        logging.critical('Finish to transfer %f %s to %s, block_num: %d, memo: %s',
            trx['amount'], trx['asset'], trx['to'], trx['block_num'], trx['memo'])

    async def on_receive(self, trx):
        """ 接收资产
        """
        logging.critical('Finish to receive %f %s from %s, block_num: %d, memo: %s',
            trx['amount'], trx['asset'], trx['from'], trx['block_num'], trx['memo'])

    async def get_asset_info(self, asset_id):
        """ 获取资产信息
        """
        if asset_id not in self.asset_info:
            asset = (await self.node_api.get_objects([asset_id]))[0]
            self.asset_info[asset_id] = asset
            self.asset_info[asset['symbol']] = asset
        return self.asset_info[asset_id]

    async def process_operations(self, op_id):
        """ 处理操作
        """
        op_info = await self.node_api.get_objects([op_id])
        for operation in op_info[::-1]:
            if operation["op"][0] != 0:
                return

            # 操作基本信息
            trx = {}
            op = operation['op'][1]
            trx['trx_id'] = operation['id']

            # 获取区块信息
            trx['block_num'] = operation['block_num']  
            block_info = await self.node_api.get_block(trx['block_num'])
            trx['timestamp'] = block_info['timestamp']

            # 获取转账金额
            asset = await self.get_asset_info(op['amount']['asset_id'])
            trx['asset'] = asset['symbol']
            trx['asset_id'] = op['amount']['asset_id']
            trx['amount'] = float(op['amount']['amount'])/float(
                10**int(asset['precision']))

            # 获取转账手续费
            trx['fee'] = {}
            fee = await self.get_asset_info(op['fee']['asset_id'])
            trx['fee']['asset'] = fee['symbol']
            trx['fee']['asset_id'] = op['fee']['asset_id']
            trx['fee']['amount'] = float(op['fee']['amount'])/float(
                10**int(fee['precision']))
         
            # 获取涉案账户
            trx['to_id'] = op['to']
            trx['from_id'] = op['from']
            trx['to'] = (await self.node_api.get_objects([op['to']]))[0]['name']
            trx['from'] = (await self.node_api.get_objects([op['from']]))[0]['name']

            # 解码备注信息
            if 'memo' in op:
                memo = op['memo']
                trx['nonce'] = memo['nonce']
                try:
                    privkey = PrivateKey(self.wifkey)
                    prefix = self.node_api.chain_params['prefix']
                    if trx['to_id'] == self.account['id']:
                        pubkey = PublicKey(memo['from'], prefix=prefix)
                    else:
                        pubkey = PublicKey(memo['to'], prefix=prefix)
                    trx['memo'] = BtsMemo.decode_memo(
                        privkey, pubkey, memo['nonce'], memo['message'])
                except Exception:
                    trx['memo'] = None
            else:
                trx['memo'] = None
                trx['nonce'] = None

            # 触发转账事件
            if trx['from_id'] == self.account['id']:
                await self.on_sent(trx)
            elif trx['to_id'] == self.account['id']:
                await self.on_receive(trx)
