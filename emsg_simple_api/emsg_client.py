#/usr/bin/env python
#coding=utf8

import json
import uuid
import logging
from thrift import Thrift
from thrift.protocol import TBinaryProtocol
from thrift.transport import TSocket, TTransport
from emsg_inf_push import emsg_inf_push
from emsg_simple_api.settings import EMSG_PUSH

logger = logging.getLogger(__name__)

#host = 'push.lcemsg.com'
#port = 4281
#licence = '8b035d3b57744b669dd8700bf694bc36'

def process(packet_str):
    '''
    发送单条消息
    后台发送消息给 emsg server, content 内容为 标准的消息结构,具体参见文档
    https://github.com/cc14514/emsg_sdk/wiki
    :param packet_str: 消息包字符串
    :return:
    '''
    try:
        transport = TSocket.TSocket(EMSG_PUSH['host'], EMSG_PUSH['port'])
        #transport = TTransport.TBufferedTransport(transport)
        transport = TTransport.TFramedTransport(transport)
        protocol = TBinaryProtocol.TBinaryProtocol(transport)
        client = emsg_inf_push.Client(protocol)
        transport.open()
        client.process(licence=EMSG_PUSH['licence'], sn=uuid.uuid4().hex, content=packet_str)
        transport.close()
        logger.debug("PUSH> %s" % packet_str)
    except Thrift.TException, tx:
        logger.error(tx.message)

def process_batch(packet_str_list):
    '''
    批量推送消息
    :param packet_str_list: 消息包字符串 组成的数组
    :return:
    '''
    try:
        transport = TSocket.TSocket(EMSG_PUSH['host'], EMSG_PUSH['port'])
        # emsg_server 采用了 buffered 传输方式
        #transport = TTransport.TBufferedTransport(transport)
        # sara server 采用了 分帧 传输方式
        transport = TTransport.TFramedTransport(transport)
        protocol = TBinaryProtocol.TBinaryProtocol(transport)
        client = emsg_inf_push.Client(protocol)
        transport.open()
        client.process_batch(licence=EMSG_PUSH['licence'], sn=uuid.uuid4().hex, content=packet_str_list)
        transport.close()
        logger.debug("PUSH_MORE> %s" % len(packet_str_list))
    except Thrift.TException, tx:
        logger.error(tx.message)

