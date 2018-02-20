# -*- coding:utf-8 -*- 

import time
import random
import asyncio
from . import asyncrpc, builder
from collections import deque
from bitsharesbase import operations
from bitsharesbase import memo as BtsMemo
from bitsharesbase.account import PrivateKey, PublicKey

class Sender(object):
    """ 发送资产
        :param url 节点地址
        :param account 账户名称
        :param wifkey 账户私钥
    """
    loop = None
    wifkey = None
    node_api = None
    asset_info = {}
    account = {'name': None, 'options': {
        'memo_key': None
    }}
    
    def __init__(self, url, account, wifkey, loop=None, num_workers=10):
        self.loop = loop
        self.wifkey = wifkey
        self.account['name'] = account
        self.__message_queue = deque()
        self.__num_workers = num_workers
        self.node_api = asyncrpc.AsyncRPC(url, loop)
        self.node_api.set_open_callback(self._on_open)

    def future_list(self):
        """ 任务列表
        """
        workers = []
        for i in range(self.__num_workers):
            workers.append(asyncio.ensure_future(self.__worker(), loop=self.loop))
        return self.node_api.future_list() + workers

    def send_asset(self, to, asset_id, amount, memo=''):
        """ 发送资产
        """
        future = asyncio.Future()
        message = (future, (to, asset_id, amount, memo))
        self.__message_queue.append(message)
        return future

    async def get_asset_info(self, asset_id):
        """ 获取资产信息
        """
        if asset_id not in self.asset_info:
            asset = (await self.node_api.get_objects([asset_id]))[0]
            self.asset_info[asset_id] = asset
            self.asset_info[asset['symbol']] = asset
        return self.asset_info[asset_id]

    async def get_transfer_fee(self):
        """ 获取转账费用
        """
        obj = (await self.node_api.get_objects(['2.0.0']))[0]
        fees = obj['parameters']['current_fees']['parameters']
        scale = float(obj['parameters']['current_fees']['scale'])
        for f in fees:
            if f[0] == 0:
                return (f[1], scale)
        raise RuntimeError('Invalid result!')

    async def calcul_transfer_fees(self, assets:list):
        """ 计算转账费用
        """
        # 获取转账费用
        fee, scale = await self.get_transfer_fee()

        # 计算转账费用
        fees = []
        for assetInfo in await self.node_api.lookup_asset_symbols(assets):
            precision   = assetInfo['precision']
            base        = assetInfo['options']['core_exchange_rate']['base']
            quote       = assetInfo['options']['core_exchange_rate']['quote']

            total = (float(base['amount'])*(fee['fee']+fee['price_per_kbyte']))/float(quote['amount'])
            total = total*scale/1e4/10**precision
            fees.append((assetInfo['id'], round(total,2)))
        return fees

    async def __encrypt_memo(self, to, memo):
        """ 加密备注
        """
        if not memo:
            return None
        # 生成nonce
        nonce = str(random.getrandbits(64))
        if self.wifkey == None:
            raise MissingKeyError('Memo key {0} missing!'.format(self.account['name']))

        # 加密备注信息
        prefix = self.node_api.chain_params['prefix']
        to_account = await self.node_api.get_account_by_name(to)
        enc = BtsMemo.encode_memo(
            PrivateKey(self.wifkey, prefix=prefix),
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

    async def __on_send_asset(self, to, asset_id, amount, memo=''):
        """ 发送资产
        """
        # 加密备注
        to_id = None
        memo_data = None
        if memo != '':
            to_id, memo_data = await self.__encrypt_memo(to, memo)
        else:
            to_account = await self.node_api.get_account_by_name(to)
            to_id = to_account['id']

        # 计算转账数量
        asset = await self.get_asset_info(asset_id)
        amount = amount * 10 ** asset['precision']

        # 生成转账操作
        prefix = self.node_api.chain_params['prefix']
        op = operations.Transfer(**{
            'to': to_id,
            'from': self.account['id'],
            'amount': {
                'amount': amount,
                'asset_id': asset_id
            },
            'prefix': prefix,
            'memo': memo_data,
            'fee': {'amount': 0, 'asset_id': asset_id}
        })

        # 执行转账操作
        txbuffer = builder.Builder(self.node_api)
        txbuffer.append_ops(op)
        await txbuffer.append_signer(self.account, self.wifkey, prefix, 'active')
        await txbuffer.sign(asset_id, expiration=600)
        res = await txbuffer.broadcast()
        return res.json()

    async def __worker(self):
        """ 工作协程
        """
        while True:
            if len(self.__message_queue) == 0:
                await asyncio.sleep(0.001)
            else:
                (future, (to, asset_id, amount, memo)) = self.__message_queue.popleft()
                try:
                    res = await self.__on_send_asset(to, asset_id, amount, memo)
                    future.set_result(res)
                except Exception as e:
                    future.set_result(e)

    async def _on_open(self, node_api):
        """ 打开连接
        """
        self.account = await self.node_api.get_account_by_name(self.account['name'])
