#/usr/bin/env python
#coding=utf8

import json
import uuid

from thrift import Thrift
from thrift.protocol import TBinaryProtocol
from thrift.transport import TSocket, TTransport
from emsg_inf_push import emsg_inf_push

host = 'push.lcemsg.com'
port = 4281
licence = '8b035d3b57744b669dd8700bf694bc36'

def process(packet_str):
    '''
    发送单条消息
    后台发送消息给 emsg server, content 内容为 标准的消息结构,具体参见文档
    https://github.com/cc14514/emsg_sdk/wiki
    :param packet_str: 消息包字符串
    :return:
    '''
    try:
        transport = TSocket.TSocket(host, port)
        transport = TTransport.TBufferedTransport(transport)
        protocol = TBinaryProtocol.TBinaryProtocol(transport)
        client = emsg_inf_push.Client(protocol)
        transport.open()
        client.process(licence=licence, sn=uuid.uuid4().hex, content=packet_str)
        transport.close()
    except Thrift.TException, tx:
        print '%s' % (tx.message)

def process_batch(packet_str_list):
    '''
    批量推送消息
    :param packet_str_list: 消息包字符串 组成的数组
    :return:
    '''
    try:
        transport = TSocket.TSocket(host, port)
        transport = TTransport.TBufferedTransport(transport)
        protocol = TBinaryProtocol.TBinaryProtocol(transport)
        client = emsg_inf_push.Client(protocol)
        transport.open()
        client.process_batch(licence=licence, sn=uuid.uuid4().hex, content=packet_str_list)
        transport.close()
    except Thrift.TException, tx:
        print '%s' % (tx.message)

