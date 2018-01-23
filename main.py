# -*- coding:utf-8 -*-

import os
import yaml
import proto
import asyncio
import logging
import casino_pb2
from monitor import sender
from monitor import rpc_client
from monitor import rpc_server
from monitor.logger import Logger
from monitor.transfer import Transfer
from logging.handlers import RotatingFileHandler

# 读取配置
config = None
with open('config.yml', 'rb') as handle:
    config = yaml.load(handle)

def initlog():
    """ 初始日志
    """
    # 日志格式
    fmt = '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s'
    formatter = logging.Formatter(fmt)

    # 终端输出
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    console.setLevel(logging.INFO)
    logging.getLogger().addHandler(console)

    # 文件输出
    logpath = 'logs/log.txt'
    dir, filename = os.path.split(logpath)
    os.makedirs(dir, exist_ok=True)
    handler = RotatingFileHandler(logpath, maxBytes=10*1024*1024, backupCount=100)
    handler.setLevel(logging.INFO)
    handler.setFormatter(formatter)

    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.NOTSET)

class Monitor(Transfer):
    """ 资产监控
    """
    def __init__(self, client, *args, **kwargs):
        super(Monitor, self).__init__(*args, **kwargs)
        self._client = client
        cnf = config['mysql_logger']
        self._logger = Logger(cnf['host'], cnf['port'], cnf['user'],
            cnf['passwd'], cnf['database'])

    def future_list(self):
        """ 任务列表
        """
        futures = super(Monitor, self).future_list()
        return self._logger.future_list() + futures

    async def on_sent(self, trx):
        """ 发送资产
        """
        await super(Monitor, self).on_sent(trx)
        self._logger.write(trx)
        request = casino_pb2.SentNoticeRequest(
            asset_id     = trx['asset_id'],
            asset        = trx['asset'],
            amount       = int(trx['amount']*100),
            fee_asset_id = trx['fee']['asset_id'],
            fee_asset    = trx['fee']['asset'],
            fee_amount   = int(trx['fee']['amount']*100),
            block_num    = trx['block_num'],
            memo         = trx['memo']
        )
        self._client.SentNotice(request)

    async def on_receive(self, trx):
        """ 接收资产
        """
        await super(Monitor, self).on_receive(trx)
        self._logger.write(trx)
        request = casino_pb2.ReceiveNoticeRequest(
            asset_id    = trx['asset_id'],
            asset       = trx['asset'],
            amount      = int(trx['amount']*100),
            block_num   = trx['block_num'],
            memo        = trx['memo']
        )
        self._client.ReceiveNotice(request)

async def event_loop(futures):
    """ 事件循环
    """
    await asyncio.wait(futures)

def main():
    """ 主函数
    """

    # 初始日志
    initlog()

    # 启动服务
    try:
        # 创建监控
        client = rpc_client.new_client(config['casino_address'],
            config['casino_port'])
        monitor = Monitor(client, config['url'], config['account'], config['wifkey'])
        futures = monitor.future_list()

        # 创建gRPC服务
        loop = asyncio.new_event_loop()
        instance = sender.Sender(config['url'], config['account'], config['wifkey'], loop)
        server = rpc_server.new_server(instance, config['bind_address'], config['port'])
        server.start()

        # 进入事件循环
        logging.info('Bitshares wallet monitor started, grpc listen: %s:%d',
            config['bind_address'], config['port'])
        asyncio.get_event_loop().run_until_complete(event_loop(futures))
    except Exception as e:
        logging.critical('Program exception exit, {0}'.format(str(e)))

if __name__ == '__main__':
    main()
