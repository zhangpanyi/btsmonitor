# -*- coding:utf-8 -*-

import struct
from binascii import unhexlify
from bitsharesbase.objects import Asset
from graphenebase.transactions import formatTimeFromNow

async def get_block_params(client):
    ''' 获取区块参数
    '''
    properties = await client.get_dynamic_global_properties()
    ref_block_num = properties['head_block_number'] & 0xFFFF
    ref_block_prefix = struct.unpack_from('<I', unhexlify(properties['head_block_id']), 4)[0]
    return ref_block_num, ref_block_prefix

async def add_required_fees(client, ops, asset_id='1.3.0'):
    ''' 添加必要手续费
    '''
    fees = await client.get_required_fees([i.json() for i in ops], asset_id)
    for i, d in enumerate(ops):
        if isinstance(fees[i], list):
            ops[i].op.data['fee'] = Asset(
                amount=fees[i][0]['amount'],
                asset_id=fees[i][0]['asset_id']
            )

            for j, _ in enumerate(ops[i].op.data['proposed_ops'].data):
                ops[i].op.data['proposed_ops'].data[j].data['op'].op.data['fee'] = (
                    Asset(
                        amount=fees[i][1][j]['amount'],
                        asset_id=fees[i][1][j]['asset_id']))
        else:
            ops[i].op.data['fee'] = Asset(
                amount=fees[i]['amount'],
                asset_id=fees[i]['asset_id']
            )
    return ops
