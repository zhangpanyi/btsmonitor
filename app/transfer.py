# -*- coding:utf-8 -*-

import random
from .sysconfig import SysConfig
from .builder import Builder, MissingKeyError
from bitsharesbase import operations
from bitsharesbase import memo as BtsMemo
from bitsharesbase.account import PrivateKey, PublicKey

class Transfer(object):
    ''' 转账模块
        :param client RPC客户端
    '''

    def __init__(self, client, account):
        self.client = client
        self.account = account

    async def send_to(self, to, asset, amount, memo=''):
        ''' 发送资产
        '''
        # 加密备注
        to_id = None
        memo_data = None
        if memo != '':
            to_id, memo_data = await self._encrypt_memo(to, memo)
        else:
            to_account = await self.client.get_account_by_name(to)
            to_id = to_account['id']

        # 计算转账数量
        amount = amount * 10 ** asset['precision']

        # 生成转账操作
        prefix = self.client.chain_params['prefix']
        op = operations.Transfer(**{
            'to': to_id,
            'from': self.account['id'],
            'amount': {
                'amount': amount,
                'asset_id': asset['id']
            },
            'prefix': prefix,
            'memo': memo_data,
            'fee': {'amount': 0, 'asset_id': asset['id']}
        })

        # 执行转账操作
        txbuffer = Builder(self.client)
        txbuffer.append_ops(op)
        await txbuffer.append_signer(self.account, SysConfig().active_key, prefix, 'active')
        await txbuffer.sign(asset['id'], expiration=600)
        res = await txbuffer.broadcast()
        return res.json()

    async def _encrypt_memo(self, to, memo):
        ''' 加密备注信息
        '''
        if not memo:
            return None

        # 生成nonce
        nonce = str(random.getrandbits(64))
        if SysConfig().memo_key == None:
            raise MissingKeyError('Memo key {0} missing!'.format(SysConfig().account))

        # 加密备注信息
        prefix = self.client.chain_params['prefix']
        to_account = await self.client.get_account_by_name(to)
        enc = BtsMemo.encode_memo(
            PrivateKey(SysConfig().memo_key, prefix=prefix),
            PublicKey(
                prefix=prefix,
                pk=to_account['options']['memo_key']
            ),
            nonce,
            memo
        )

        # 返回结构信息
        memo_data = {
            'nonce': nonce,
            'message': enc,
            'to': to_account['options']['memo_key'],
            'from': self.account['options']['memo_key']
        }
        return to_account['id'], memo_data
