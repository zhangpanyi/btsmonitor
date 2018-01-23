# -*- coding:utf-8 -*- 

import grpc
import asyncio
import logging
import wallet_pb2
import wallet_pb2_grpc
from bitshares.dex import Dex
from concurrent import futures
from .executor import AsyncioExecutor

def new_server(sender, address, port):
    """ 新建服务
    """
    sender.future_list()
    server = grpc.server(AsyncioExecutor(loop=sender.loop))
    wallet_pb2_grpc.add_WalletServicer_to_server(WalletServicer(sender), server)
    server.add_insecure_port(address + ':' + str(port))
    return server

class WalletServicer(wallet_pb2_grpc.WalletServicer):
    """ 钱包服务
    """
    def __init__(self, sender):
        self._sender = sender

    async def GetFees(self, request, context):
        """ 获取费用
        """
        try:
            fees = []
            assets = []
            for asset in request.assets:
                assets.append(asset)
            for asset_id, fee in await self._sender.calcul_transfer_fees(assets):
                fees.append(wallet_pb2.Fee(asset_id=asset_id, fee=int(fee*100)))
            return wallet_pb2.GetFreeReply(ok=True, fees=fees)
        except Exception as e:
            logging.info('GetFees exception, %s', str(e))
            return wallet_pb2.GetFreeReply(ok=False, reason=str(e))

    async def Transfer(self, request, context):
        """ 转账操作
        """
        try:
            amount = request.amount / 100.0
            future = self._sender.send_asset(request.to, request.asset_id,
                amount, request.memo)
            await asyncio.wait_for(future, None)
            ret = future.result()
            if isinstance(ret, Exception):
                logging.info('Transfer exception, %s', str(ret))
                return wallet_pb2.TransferReply(ok=False, reason=str(ret))
            return wallet_pb2.TransferReply(ok=True)
        except Exception as e:
            logging.info('Transfer exception, %s', str(e))
            return wallet_pb2.TransferReply(ok=False, reason=str(e))
