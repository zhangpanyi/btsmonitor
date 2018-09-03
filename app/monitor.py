# -*- coding:utf-8 -*-

import asyncio
import logging
from .pusher import Pusher
from .asyncrpc import AsyncRPC
from .sysconfig import SysConfig
from bitsharesbase import memo as BtsMemo
from bitsharesbase.account import PublicKey, PrivateKey

def get_operation_id(id):
    ''' 获取操作id
    '''
    return int(id.split('.')[2])

def make_operation_id(id):
    ''' 生成操作id
    '''
    return '.'.join(['1', '11', str(id)])

class Monitor(object):
    ''' 资产监控
        :param account 比特股账户名
    '''
    asset_info = {}

    TRANSFER_OPERATION = 0
    OPERATION_HISTORY_ID_TYPE = '1.11.0'

    def __init__(self, access, account, loop=None):
        self._loop = loop
        self._account = None
        self._access = access
        self._account_name = account
        self._last_relative_position = 0
        self._pusher = Pusher(self._loop)
        if self._loop is None:
            self._loop = asyncio.get_event_loop()
        asyncio.ensure_future(
            self._listen_for_activity(), loop=self._loop)

    async def _get_history_operation(self, client, op_number, limit):
        ''' 获取历史操作
        '''
        history = client.api_id['history']
        operations = await client.get_relative_account_history(
            self._account['id'], op_number, limit, op_number+limit, api_id=history)
        return operations

    async def _get_asset_info(self, client, asset_id):
        ''' 获取资产信息
        '''
        if asset_id not in self.asset_info:
            asset = (await client.get_objects([asset_id]))[0]
            self.asset_info[asset_id] = asset
            self.asset_info[asset['symbol']] = asset
        return self.asset_info[asset_id]

    async def _process_transfer_operations(self, client, operation):
        ''' 处理转账操作
        '''
        # 筛选操作类型
        if operation['op'][0] != self.TRANSFER_OPERATION:
            return

        # 操作基本信息
        trx = {}
        op = operation['op'][1]
        trx['txid'] = operation['id']
        
        # 获取区块信息
        trx['heigth'] = operation['block_num']  
        block_info = await client.get_block(trx['block_num'])
        trx['timestamp'] = block_info['timestamp']
        
        # 获取转账金额
        asset = await self._get_asset_info(client, op['amount']['asset_id'])
        trx['asset'] = asset['symbol']
        trx['asset_id'] = op['amount']['asset_id']
        trx['amount'] = str(float(op['amount']['amount'])/float(
            10**int(asset['precision'])))
        
        # 获取转账手续费
        trx['fee'] = {}
        fee = await self._get_asset_info(client, op['fee']['asset_id'])
        trx['fee']['asset'] = fee['symbol']
        trx['fee']['asset_id'] = op['fee']['asset_id']
        trx['fee']['amount'] = str(float(op['fee']['amount'])/float(
            10**int(fee['precision'])))
       
        # 获取涉案账户
        trx['to_id'] = op['to']
        trx['from_id'] = op['from']
        trx['to'] = (await client.get_objects([op['to']]))[0]['name']
        trx['from'] = (await client.get_objects([op['from']]))[0]['name']
        
        # 解码备注信息
        if 'memo' in op:
            memo = op['memo']
            trx['nonce'] = memo['nonce']
            try:
                privkey = PrivateKey(SysConfig().memo_key)
                prefix = client.chain_params['prefix']
                if trx['to_id'] == self._account['id']:
                    pubkey = PublicKey(memo['from'], prefix=prefix)
                else:
                    pubkey = PublicKey(memo['to'], prefix=prefix)
                trx['memo'] = BtsMemo.decode_memo(
                    privkey, pubkey, memo['nonce'], memo['message'])
            except Exception as e:
                logging.warn('Failed to decode memo, %s, %s', operation['id'], str(e))
                trx['memo'] = None
        else:
            trx['memo'] = None
            trx['nonce'] = None
        return trx

    async def _get_and_process_operations(self, client, op_number):
        ''' 获取并处理操作
        '''
        while True:
            # 获取历史操作
            operations = None
            try:
                operations = await self._get_history_operation(client, op_number, 100)
                if len(operations) == 0:
                    break
            except Exception as e:
                logging.warn('Failed to get history operation, %s', str(e))
                break

            # 处理转账操作
            index = 0
            operations = operations[::-1]
            while index < len(operations):
                operation = operations[index]
                try:
                    trx = await self._process_transfer_operations(client, operation)
                    if not trx is None:
                        logging.info('New transfer operation: %s', trx)
                        self._pusher.async_call(trx)
                    index += 1
                    op_number += 1
                    SysConfig().update_last_op_number(op_number)
                except Exception as e:
                    logging.warn('Failed to get process operation#%s, %s', operation['id'], str(e))
                    continue
        return op_number

    async def _listen_for_activity(self):
        ''' 监听账户活动
        '''
        op_number = SysConfig().get_last_op_number()
        while True:
            # 创建客户端
            client = AsyncRPC(self._access, self._loop)
            if not await client.wait_for_ready():
                continue

            # 获取账户信息
            if self._account is None:
                try:
                    self._account = await client.get_account_by_name(self._account_name)
                except Exception as e:
                    logging.warn('Failed to get account by name, %s', str(e))
                    continue

            # 获取账户统计
            try:
                [statistics] = await client.get_objects([self._account['statistics']])
                if op_number <= statistics['removed_ops']:
                    op_number = statistics['removed_ops'] + 1
                if op_number > statistics['total_ops']:
                    await client.close()
                    await asyncio.sleep(10)
                    continue
            except Exception as e:
                logging.warn('Failed to get statistics#%s object, %s', self._account['statistics'], str(e))
                continue

            # 获取并处理操作
            op_number = await self._get_and_process_operations(client, op_number)

            # 关闭客户端
            await client.close()
            logging.info('Account#%s current op number: %d', self._account_name, op_number)
