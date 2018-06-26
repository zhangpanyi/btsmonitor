# -*- coding:utf-8 -*-

import asyncio
from aiohttp.web import Application
from aiohttp_json_rpc import JsonRpc

class RpcServer(object):
    ''' json-rpc服务
    '''

    def __init__(self, loop=None):
        # 初始化
        self._loop = loop
        if self._loop is None:
            self._loop = asyncio.get_event_loop()
        self._started = False

        # 添加方法
        self._rpc = JsonRpc()
        self._rpc.add_methods(
            ('', self.ping),
        )

    def listen(self, host, port):
        ''' 监听服务
        '''
        if not self._started:
            app = Application(loop=self._loop)
            app.router.add_route('*', '/', self._rpc)
            self._loop.create_server(app.make_handler(), host, port)
            self._started = True

    async def ping(self, request):
        return 'pong'
