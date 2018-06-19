# -*- coding:utf-8 -*-

import asyncio
import logging
from app import logger
from app.monitor import Monitor
from app.sysconfig import SysConfig

async def event_loop(futures):
    ''' 事件循环
    '''
    try:
        await asyncio.wait(futures)
    except Exception as e:
        logging.critical('Event loop error, %s', str(e))

def main():
    # 初始配置
    sysconfig = SysConfig()

    # 运行监控
    monitor = Monitor(sysconfig.wss, sysconfig.account)
    
    # 进入事件循环
    try:
        futures = monitor.get_futures()
        asyncio.get_event_loop().run_until_complete(event_loop(futures))
    except Exception as e:
        logging.critical('Event loop error, %s', str(e))

if __name__ == '__main__':
    main()
