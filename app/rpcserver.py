# -*- coding:utf-8 -*-

import asyncio
from aiohttp import web
from .asyncrpc import AsyncRPC
from .transfer import Transfer
from .sysconfig import SysConfig
from jsonrpcserver.aio import methods

@methods.add
async def account(context):
    ''' 账户信息
    '''
    return SysConfig().account

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
            'amount': str(float(asset['amount'])/float(10**int(asset_info['precision'])))
        })
    return result

@methods.add
async def transfer(to, symbol_or_id, amount, memo, context):
    ''' 资产转账
    '''
    client = context['client']
    server = context['server']
    account = await server.account_info(client)
    asset = await server.get_asset_info(client, symbol_or_id)
    transfer = Transfer(client, account)
    return await transfer.send_to(to, asset, float(amount), memo)

@methods.add
async def get_transfer_fees(symbols_or_ids : list, context):
    ''' 获取转账手续费
    '''
    assets = []
    client = context['client']
    server = context['server']
    for asset in symbols_or_ids:
        assets.append(await server.get_asset_info(client, asset))
    return await server.calcul_transfer_fees(client, assets)

class RpcServer(object):
    ''' json-rpc服务
    '''
    asset_info = {}

    def __init__(self, loop=None):
        self._loop = loop
        if self._loop is None:
            self._loop = asyncio.get_event_loop()
        self._started = False
        self._account_info = None

    def listen(self, host, port):
        ''' 监听服务
        '''
        if not self._started:
            app = web.Application(loop=self._loop)
            app.router.add_post('/', self._handle)
            self._loop.run_until_complete(
                self._loop.create_server(app.make_handler(), host, port))
            self._started = True

    async def account_info(self, client):
        if self._account_info is None:
            self._account_info = await client.get_account_by_name(SysConfig().account)
        return self._account_info

    async def get_asset_info(self, client, symbol_or_id):
        ''' 获取资产信息
        '''
        if symbol_or_id not in self.asset_info:
            asset = (await client.lookup_asset_symbols([symbol_or_id]))[0]
            self.asset_info[asset['id']] = asset
            self.asset_info[asset['symbol']] = asset
        return self.asset_info[symbol_or_id]


    async def get_transfer_fee(self, client):
        ''' 获取转账费用
        '''
        obj = (await client.get_objects(['2.0.0']))[0]
        fees = obj['parameters']['current_fees']['parameters']
        scale = float(obj['parameters']['current_fees']['scale'])
        for f in fees:
            if f[0] == 0:
                return (f[1], scale)
        raise RuntimeError('Invalid result!')

    async def calcul_transfer_fees(self, client, assets):
        ''' 计算转账费用
        '''
        fee_list = []
        fee, scale = await self.get_transfer_fee(client)
        for asset_info in assets:
            precision   = asset_info['precision']
            base        = asset_info['options']['core_exchange_rate']['base']
            quote       = asset_info['options']['core_exchange_rate']['quote']

            total = (float(base['amount'])*(fee['fee']+fee['price_per_kbyte']))/float(quote['amount'])
            total = total*scale/1e4/10**precision
            fee_list.append(str(round(total, 2)))
        return fee_list

    async def _handle(self, request):
        ''' 分发请求
        '''
        request = await request.text()
        client = AsyncRPC(SysConfig().access, self._loop)
        if not await client.wait_for_ready():
            raise RuntimeError('Websocket connection failed')
        response = await methods.dispatch(request, context={'server': self, 'client': client})
        await client.close()
        if response.is_notification:
            return web.Response()
        else:
            return web.json_response(response, status=response.http_status)
