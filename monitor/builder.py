# -*- coding:utf-8 -*- 

from . import transactions
from bitsharesbase import operations
from bitsharesbase.objects import Operation
from bitsharesbase.account import PrivateKey
from bitsharesbase.signedtransactions import Signed_Transaction

class MissingKeyError(Exception):
    pass

class Builder(dict):
    """ 操作构建器
    """
    ops = []
    wifs = []
    node_api = None
    available_signers = []

    def __init__(self, node_api):
        self.node_api = node_api

    def json(self):
        return dict(self)
    
    def clear(self):
        """ 清理
        """
        self.ops = []
        self.wifs = []
        self.available_signers = []
    
    def append_ops(self, ops):
        """ 添加操作
        """
        if isinstance(ops, list):
            self.ops.extend(ops)
        else:
            self.ops.append(ops)

    async def append_signer(self, account, wifkey, prefix, permission):
        """ 添加签名
        """
        pubkey = PrivateKey(wifkey, prefix=prefix).pubkey
        required_treshold = account[permission]['weight_threshold']

        async def fetchkeys(account, perm, level=0):
            r = []
            if level > 2:
                return r
            for authority in account[perm]['key_auths']:
                if authority[0] == str(pubkey):
                    r.append([wifkey, authority[1]])
            
            if sum([x[1] for x in r]) < required_treshold:
                for authority in account[perm]['account_auths']:
                    auth_account = await self.node_api.get_account_by_name(authority[0])
                    r.extend(fetchkeys(auth_account, perm, level + 1))
            return r

        assert permission in ['active', 'owner'], 'Invalid permission'

        if account not in self.available_signers:
            keys = await fetchkeys(account, permission)
            if permission != 'owner':
                keys.extend(await fetchkeys(account, 'owner'))
            self.wifs.extend([x[0] for x in keys])
            self.available_signers.append(account)

    async def sign(self, fee_asset_id, expiration=30):
        """ 执行签名
        """
        await self.__construct_tx(fee_asset_id, expiration)
        operations.default_prefix = self.node_api.chain_params['prefix']

        try:
            signedtx = Signed_Transaction(**self.json())
        except:
            raise ValueError('Invalid TransactionBuilder Format')

        if not any(self.wifs):
            raise MissingKeyError

        signedtx.sign(self.wifs, chain=self.node_api.chain_params)
        self['signatures'].extend(signedtx.json().get('signatures'))

    async def broadcast(self):
        """ 广播操作
        """
        tx = self.json()
        try:
            await self.node_api.broadcast_transaction(tx, api="network_broadcast")
        except Exception as e:
            raise e
        self.clear()
        return self

    async def __construct_tx(self, fee_asset_id, expiration):
        """ 构造转账操作
        """
        ops = [Operation(o) for o in list(self.ops)]
        expiration = transactions.formatTimeFromNow(expiration)
        ops = await transactions.add_required_fees(self.node_api, ops, fee_asset_id)
        ref_block_num, ref_block_prefix = await transactions.get_block_params(self.node_api)
        tx = Signed_Transaction(
            ref_block_num=ref_block_num,
            ref_block_prefix=ref_block_prefix,
            expiration=expiration,
            operations=ops
        )
        super(Builder, self).__init__(tx.json())
