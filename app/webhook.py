# -*- coding:utf-8 -*-

import aiohttp
import asyncio
import logging
from collections import deque
from .sysconfig import SysConfig

class Webhook(object):
    def __init__(self, loop=None):
        self._loop = loop
        self._message_queue = deque()
        if self._loop is None:
            self._loop = asyncio.get_event_loop()

    def get_futures(self):
        ''' 任务列表
        '''
        futures = []
        sysconfig = SysConfig()
        for _ in range(sysconfig.workernum):
            futures.append(asyncio.ensure_future(self._do_work()))
        return futures

    def async_call(self, trx):
        ''' 异步调用
        '''
        self._message_queue.append(trx)
    
    async def _do_work(self):
        ''' 工作协程
        '''
        while True:
            if len(self._message_queue) == 0:
                await asyncio.sleep(0.001)
                continue
            trx = self._message_queue.popleft()
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(SysConfig().webhook, json=trx)
            except Exception as e:
                logging.info('Failed to post notify: %s, %s', trx, str(e))
