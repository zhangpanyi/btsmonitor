# -*- coding:utf-8 -*-

import asyncio
from aiohttp import web
from .asyncrpc import AsyncRPC
from .sysconfig import SysConfig
from jsonrpcserver.aio import methods

@methods.add
async def get_balances(context):
    ''' 获取余额
    '''
    client = context['client']

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

class RpcServer(object):
    ''' json-rpc服务
    '''

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

    async def _handle(self, request):
        ''' 分发请求
        '''
        client = AsyncRPC(SysConfig.access, self._loop)
        await client.wait_for_ready()

        request = await request.text()
        response = await methods.dispatch(request, context={'client': client})
        if response.is_notification:
            return web.Response()
        else:
            return web.json_response(response, status=response.http_status)
