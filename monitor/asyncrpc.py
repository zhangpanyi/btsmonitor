# -*- coding:utf-8 -*- 

import json
import asyncio
import websockets
from bitsharesbase.chains import known_chains

class RPCError(Exception):
    """ 远程过程调用错误
    """
    pass

class AsyncRPC(object):
    """ 异步RPC客户端
        :param url 节点地址
    """
    api_id = {}
    chain_params = None

    def __init__(self, url, loop=None):
        self.url= url
        self.__loop = loop
        self.__result = {}
        self.__request_id = 0
        self.__websocket = None
        self.__open_callback = None

    def future_list(self):
        """ 任务列表
        """
        return [asyncio.ensure_future(self._handler(), loop=self.__loop)]

    def set_open_callback(self, cb):
        """ 设置回调
        """
        self.__open_callback = cb

    def on_messsage(self, payload):
        """ 收到消息
        """
        res = json.loads(payload)
        if 'id' in res  and res['id'] in self.__result:
            self.__result[res['id']].set_result(res)

    async def _on_open(self):
        """ 连接成功
        """
        await self.__rpc([1, 'login', ['', '']])

        # 获取API信息
        self.api_id['history'] = await self.history(api_id=1)
        self.api_id['database'] = await self.database(api_id=1)
        self.api_id['network_broadcast'] = await self.network_broadcast(api_id=1)

        # 获取网络信息
        props = await self.get_chain_properties(api_id=0)
        chain_id = props["chain_id"]
        for k, v in known_chains.items():
            if v["chain_id"] == chain_id:
                self.chain_params = v
                break
        if self.chain_params == None:
            raise("Connecting to unknown network!")

        if self.__open_callback != None:
            await self.__open_callback(self)

    async def __keep_alive(self):
        """ 保持活跃
        """
        while True:   
            await self.get_chain_id()
            await asyncio.sleep(10)

    async def __handler_message(self):
        """ 消息处理
        """
        while True:
            payload = await self.__websocket.recv()
            self.on_messsage(payload)

    async def _handler(self):
        """ 事件循环
        """
        async with websockets.connect(self.url, max_size=2**20*8, max_queue=2**5*2) as websocket:
            self.__websocket = websocket
            task1 = asyncio.ensure_future(self._on_open(), loop=self.__loop)
            task2 = asyncio.ensure_future(self.__keep_alive(), loop=self.__loop)
            task3 = asyncio.ensure_future(self.__handler_message(), loop=self.__loop)
            await asyncio.wait([task1, task2, task3])

    async def __rpc(self, params):
        """ 远程过程调用
        """
        # 生成请求id
        self.__request_id += 1
        request_id = self.__request_id

        # 生成请求内容
        request = {'id': request_id, 'method': 'call', 'params': params}
        future = self.__result[request_id] = asyncio.Future()

        # 异步执行请求
        await self.__websocket.send(json.dumps(request).encode('utf8'))
        await asyncio.wait_for(future, None)
        self.__result.pop(request_id)

        # 格式化返回结果
        ret = future.result()
        if 'error' in ret:
            if 'detail' in ret['error']:
                raise RPCError(ret['error']['detail'])
            else:
                raise RPCError(ret['error']['message'])
        return ret["result"]

    def __getattr__(self, name):
        """ 简化方法调用
        """
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
            return await self.__rpc([api_id, name, [*args]])
        return method
