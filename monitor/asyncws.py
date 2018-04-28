# -*- coding:utf-8 -*- 

import json
import asyncio
import logging
import websockets
from . import asyncrpc
from collections import deque

class AsyncWs(object):
    """ 异步WebSocket
        :param url 节点地址
    """
    history_api = 0
    network_api = 0
    database_api = 0

    def __init__(self, url, num_workers=10):
        self.url = url
        self.__result = {}
        self.__callbacks = {}
        self.__request_id = 0
        self.__websocket = None
        self.__connected = False
        self.__message_queue = deque()
        self.__num_workers = num_workers

    def future_list(self):
        """ 任务列表
        """
        workers = []
        for i in range(self.__num_workers):
            workers.append(asyncio.ensure_future(self.__worker()))
        return [asyncio.ensure_future(self._handler())] + workers

    async def rpc(self, params):
        """ 远程过程调用
        """
        # 是否连接
        if not self.__connected:
            raise websockets.ConnectionClosed(1000, '')

        # 生成请求id
        self.__request_id += 1
        request_id = self.__request_id

        # 生成请求内容
        request = {'id': request_id, 'method': 'call', 'params': params}
        future = self.__result[request_id] = asyncio.Future()

        # 异步执行请求
        try:
            await self.__websocket.send(json.dumps(request).encode('utf8'))
        except Exception as e:
            self.__websocket.close()
            self.__connected = False
            logging.info('Websocket write exception, %s', str(e))
            raise e
        await asyncio.wait_for(future, None)
        self.__result.pop(request_id)

        # 格式化返回结果
        ret = future.result()
        if 'error' in ret:
            if 'detail' in ret['error']:
                raise asyncrpc.RPCError(ret['error']['detail'])
            else:
                raise asyncrpc.RPCError(ret['error']['message'])
        return ret["result"]

    def subscribe(self, object_id, callback):
        """ 订阅消息
        """
        if object_id not in self.__callbacks:
            self.__callbacks[object_id] = [callback]
        else:
            self.__callbacks[object_id].append(callback)

    async def on_messsage(self, payload):
        """ 收到消息
        """
        res = json.loads(payload)
        if 'id' in res  and res['id'] in self.__result:
            self.__result[res['id']].set_result(res)
        elif 'method' in res:
            for notice in res['params'][1][0]:
                if 'id' not in notice:
                    if 'removed' in self.__callbacks:
                        for cb in self.__callbacks['removed']:
                            await cb(notice)
                    continue
                for id in self.__callbacks:
                    if id == notice['id'][:len(id)]:
                        for cb in self.__callbacks[id]:
                            await cb(notice)

    async def __worker(self):
        """ 工作协程
        """
        while True:
            if len(self.__message_queue) == 0:
                if not self.__connected:
                    break
                await asyncio.sleep(0.001)
            else:
                payload = self.__message_queue.popleft()
                await self.on_messsage(payload)

    async def _on_open(self):
        """ 连接成功
        """
        self.__connected = True
        await self.rpc([1, 'login', ['', '']])
        self.history_api = await self.rpc([1, 'history', []])
        self.database_api = await self.rpc([1, 'database', []])
        self.network_api = await self.rpc([1, 'network_broadcast', []])
        await self.rpc(
            [self.database_api, "set_subscribe_callback", [200, False]])

    async def __keep_alive(self):
        """ 保持活跃
        """
        while True:
            try:
                await asyncio.sleep(10)
                await self.rpc([0, 'get_chain_id', []])
            except Exception as e:
                break

    async def __handler_message(self):
        """ 消息处理
        """
        while self.__connected:
            payload = None
            try:
                payload = await self.__websocket.recv()
                self.__message_queue.append(payload) 
            except Exception as e:
                self.__websocket.close()
                self.__connected = False
                logging.info('Websocket read exception, %s', str(e))

    async def _handler(self):
        """ 事件循环
        """
        while True:
            self.__result.clear()
            async with websockets.connect(self.url, max_size=2**20*8, max_queue=2**5*2) as websocket:
                self.__websocket = websocket
                task1 = asyncio.ensure_future(self._on_open())
                task2 = asyncio.ensure_future(self.__keep_alive())
                task3 = asyncio.ensure_future(self.__handler_message())
                await asyncio.wait([task1, task2, task3])
