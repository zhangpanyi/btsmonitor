# -*- coding:utf-8 -*-

import asyncio
from aiohttp import web
from .httprpc import HttpRPC
from .sysconfig import SysConfig
from jsonrpcserver.aio import methods

@methods.add
async def get_balances(context):
    ''' 获取余额
    '''
    result = []
    client = context['client']
    server = context['server']
    balances = await client.get_named_account_balances(SysConfig().account, [])
    for asset in balances:
        asset_info = await server.get_asset_info(client, asset['asset_id'])
        result.append({
            'id': asset_info['id'],
            'symbol': asset_info['symbol'],
            'amount': float(asset['amount'])/float(10**int(asset_info['precision']))
        })
    return result

@methods.add
async def get_fee(context, symbols_or_ids):
    ''' 获取手续费
    '''
    client = context['client']

@methods.add
async def transfer(context, to, symbol_or_id, amount, memo):
    ''' 资产转账
    '''
    client = context['client']
    await client.load_chain_params()

class RpcServer(object):
    ''' json-rpc服务
    '''
    asset_info = {}

    def __init__(self, loop=None):
        self._loop = loop
        if self._loop is None:
            self._loop = asyncio.get_event_loop()
        self._started = False

    def listen(self, host, port):
        ''' 监听服务
        '''
        if not self._started:
            app = web.Application(loop=self._loop)
            app.router.add_post('/', self._handle)
            self._loop.run_until_complete(
                self._loop.create_server(app.make_handler(), host, port))
            self._started = True

    async def get_asset_info(self, client, asset_id):
        ''' 获取资产信息
        '''
        if asset_id not in self.asset_info:
            asset = (await client.get_objects([asset_id]))[0]
            self.asset_info[asset_id] = asset
            self.asset_info[asset['symbol']] = asset
        return self.asset_info[asset_id]

    async def _handle(self, request):
        ''' 分发请求
        '''
        request = await request.text()
        client = HttpRPC(SysConfig().access, self._loop)
        response = await methods.dispatch(request, context={'server': self, 'client': client})
        if response.is_notification:
            return web.Response()
        else:
            return web.json_response(response, status=response.http_status)
