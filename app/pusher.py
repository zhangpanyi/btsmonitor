# -*- coding:utf-8 -*-

import aiohttp
import asyncio
import logging
from collections import deque
from .sysconfig import SysConfig

class Pusher(object):
    ''' 通知推送器
    '''
    
    def __init__(self, loop=None):
        self._loop = loop
        self._message_queue = deque()
        if self._loop is None:
            self._loop = asyncio.get_event_loop()
        for _ in range(SysConfig().workernum):
            asyncio.ensure_future(self._do_work())

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
                    await session.post(SysConfig().webhook, json=trx)
            except Exception as e:
                logging.warn('Failed to post notify: %s, %s', trx, str(e))
