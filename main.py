# -*- coding:utf-8 -*-

import signal
import asyncio
import logging
from app import logger
from app.monitor import Monitor
from app.sysconfig import SysConfig

def handler(signum, frame):
    asyncio.get_event_loop().stop()
    logging.info('Bitshares monitor server stopped.')

def main():
    # 初始配置
    sysconfig = SysConfig()

    # 运行监控
    Monitor(sysconfig.access, sysconfig.account)
    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)

    # 进入事件循环
    try:
        logging.info('Bitshares monitor server start.')
        asyncio.get_event_loop().run_forever()
    except Exception as e:
        logging.critical('Event loop error, %s', str(e))

if __name__ == '__main__':
    main()
