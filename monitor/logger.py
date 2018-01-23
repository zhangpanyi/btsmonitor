# -*- coding:utf-8 -*- 

import asyncio
import logging
import aiomysql
from collections import deque
from aiomysql.sa import create_engine
from sqlalchemy import Table, Column, MetaData, Integer, BigInteger, String

table = Table('transfer', MetaData(),
            Column('id', BigInteger, primary_key=True, autoincrement=True),
            Column('trx_id', String(32), nullable=False),
            Column('block_num', BigInteger, nullable=False),
            Column('asset', String(64), nullable=False),
            Column('asset_id', String(64), nullable=False),
            Column('amount', Integer, nullable=False),
            Column('from_id', String(32), nullable=False),
            Column('to_id', String(32), nullable=False),
            Column('from_name', String(64), nullable=False),
            Column('to_name', String(64), nullable=False),
            Column('memo', String(255), nullable=True),
            Column('nonce', String(255), nullable=True),
            Column('timestamp', String(32), nullable=False))

class Logger(object):
    """ MySQL日志记录器
    """
    def __init__(self, host, port, user, passwd, db):
        self._db = db
        self._host = host
        self._port = port
        self._user = user
        self._passwd = passwd

        self._engine = None
        self._deque = deque()

    def future_list(self):
        """ 任务列表
        """
        return [asyncio.ensure_future(self._handler())]

    def write(self, trx):
        """ 写入日志
        """
        log = table.insert().values(
            trx_id      = trx['trx_id'],
            block_num   = trx['block_num'],
            asset       = trx['asset'],
            asset_id    = trx['asset_id'],
            amount      = trx['amount'],
            from_id     = trx['from_id'],
            to_id       = trx['to_id'],
            from_name   = trx['from'],
            to_name     = trx['to'],
            memo        = trx['memo'],
            nonce       = trx['nonce'],
            timestamp   = trx['timestamp']
        )
        self._deque.append(log)

    async def __keep_engine(self):
        """ 保持连接
        """
        while True:
            async with self._engine.acquire() as conn:
                await conn.connection.ping()
            await asyncio.sleep(60)

    async def __handler_request(self):
        """ 处理请求
        """
        while True:
            if len(self._deque) == 0:
                await asyncio.sleep(0.001)
            else:
                log = self._deque.popleft()
                try:
                    async with self._engine.acquire() as conn:
                        await conn.execute(log)
                except Exception as e:
                    logging.error('Insert log to MySQL exception, %s', str(e))

    async def _handler(self):
        """ 事件循环
        """
        self._engine = await create_engine(host=self._host, port=self._port,
            user=self._user, password=self._passwd, db=self._db, autocommit=True)
        task1 = asyncio.ensure_future(self.__keep_engine())
        task2 = asyncio.ensure_future(self.__handler_request())
        await asyncio.wait([task1, task2])
