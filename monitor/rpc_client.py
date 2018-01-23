# -*- coding:utf-8 -*-

import grpc
import casino_pb2_grpc

def new_client(address, port):
    """ 新建客户端
    """
    conn = grpc.insecure_channel(address + ':' + str(port))
    return casino_pb2_grpc.CasinoStub(conn)
