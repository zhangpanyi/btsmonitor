# -*- coding:utf-8 -*-

import json
import asyncio
import websockets
from bitsharesbase.chains import known_chains

class RPCError(Exception):
    pass

class AsyncRPC(object):
    ''' 异步RPC客户端
        :param url 节点地址
    '''
    api_id = {}
    chain_params = None

    def __init__(self, access, loop=None):
        self.url = 'wss://' + access
        self._loop = loop
        self._result = {}
        self._request_id = 0
        self._websocket = None
        if self._loop is None:
            self._loop = asyncio.get_event_loop()
        self._almost_ready = asyncio.Future(loop=self._loop)
        asyncio.ensure_future(self._open_connection(), loop=self._loop)

    async def close(self):
        await self._websocket.close()

    async def wait_for_ready(self):
        ''' 等待就绪
        '''
        return await asyncio.wait_for(self._almost_ready, None)

    async def _on_open(self):
        ''' 连接成功
        '''
        await self._rpc([1, 'login', ['', '']])
        self.api_id['history'] = await self.history(api_id=1)
        self.api_id['database'] = await self.database(api_id=1)
        self.api_id['network_broadcast'] = await self.network_broadcast(api_id=1)

        props = await self.get_chain_properties(api_id=0)
        chain_id = props['chain_id']
        for k, v in known_chains.items():
            if v['chain_id'] == chain_id:
                self.chain_params = v
                break
        if self.chain_params == None:
            raise('Connecting to unknown network!')

        self._almost_ready.set_result(True)

    def _on_messsage(self, payload):
        ''' 收到消息
        '''
        res = json.loads(payload)
        if 'id' in res  and res['id'] in self._result:
            self._result[res['id']].set_result(res)

    async def _recv_message(self):
        ''' 接收消息
        '''
        while True:
            try:
                payload = await self._websocket.recv()
                self._on_messsage(payload)
            except websockets.ConnectionClosed:
                break

    async def _open_connection(self):
        ''' 打开连接
        '''
        try:
            async with websockets.connect(self.url, max_size=2**20*8, max_queue=2**5*2) as websocket:
                self._websocket = websocket
                task1 = asyncio.ensure_future(self._on_open(), loop=self._loop)
                task2 = asyncio.ensure_future(self._recv_message(), loop=self._loop)
                await asyncio.wait([task1, task2])
        except Exception:
            self._almost_ready.set_result(False)

    async def _rpc(self, params):
        ''' 远程过程调用
        '''
        # 生成请求id
        self._request_id += 1
        request_id = self._request_id

        # 生成请求内容
        request = {'id': request_id, 'method': 'call', 'params': params}
        future = self._result[request_id] = asyncio.Future(loop=self._loop)

        # 异步执行请求
        await self._websocket.send(json.dumps(request).encode('utf8'))
        await asyncio.wait_for(future, None)
        self._result.pop(request_id)

        # 格式化返回结果
        ret = future.result()
        if 'error' in ret:
            if 'detail' in ret['error']:
                raise RPCError(ret['error']['detail'])
            else:
                raise RPCError(ret['error']['message'])
        return ret['result']

    def __getattr__(self, name):
        ''' 简化方法调用
        '''
        async def method(*args, **kwargs):
            api_id = 0
            if 'api_id' not in kwargs:
                if ('api' in kwargs):
                    if (kwargs['api'] in self.api_id and
                            self.api_id[kwargs['api']]):
                        api_id = self.api_id[kwargs['api']]
                    else:
                        raise ValueError(
                            'Unknown API! '
                            'Verify that you have registered to %s'
                            % kwargs['api']
                        )
                else:
                    api_id = 0
            else:
                api_id = kwargs['api_id']
            return await self._rpc([api_id, name, [*args]])
        return method
