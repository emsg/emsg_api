#/usr/bin/env python
#coding=utf8

import logging
import traceback

from django.db import transaction

import errors
import uuid
import time
from models import *
from django.contrib.auth.models import User
import django.utils.timezone as dtz
logger = logging.getLogger(__name__)
from django.forms.models import model_to_dict
from django.contrib.auth import *
from service import BaseService
import json
from apns_clerk import Message, Session, APNs
from apns_clerk.apns import Result
from apns_clerk.backends.dummy import Backend as DummyBackend

'''
emsg_server 回调接口文档
https://github.com/cc14514/emsg_sdk/wiki/emsg_server-%E6%8E%A5%E5%8F%A3%E6%96%87%E6%A1%A3
'''

session = Session()
# push_sandbox 测试证书
# push_production 生产证书
con = session.get_connection("push_sandbox", cert_file="/app/emsg_dev_APNs.pem")

class user_message(BaseService):
    def offline(self,body):
        '''
        离线消息回调,其中 params 是 packet
        :param body:
        :return:
        '''
        sn = body['sn']
        packet = body['params']
        # text image geo audio
        logger.info('[emsg_offline] packet = %s' % packet)
        self._apns_push(packet)
        return self._success(sn=sn,success=True)

    def _apns_push(self,packet):
        envelope = packet.get('envelope')
        to_jid = envelope.get('to')
        to = to_jid.split('@')[0]
        user_info = UserInfo.objects.get(id=to)
        if user_info.device_token:
            logger.info('APNS : %s' % user_info.device_token)
            device_token = user_info.device_token
            payload = packet.get('payload')
            attrs = payload.get('attrs')
            messageType = attrs.get('messageType')
            if 'text' == messageType:
                content = payload.get('content')
            elif 'image' == messageType:
                content = '收到一张图片'
            elif 'geo' == messageType:
                content = '收到一个坐标分享'
            elif 'audio' == messageType:
                content = '收到一条语音'
            elif 'contact' == messageType: # 联系人接口通知
                action = attrs.get('action')
                if 'add' == action:
                    content = '添加联系人通知'
                elif 'accept' == action:
                    content = '接受好友申请通知'
                elif 'reject' == action:
                    content = '拒绝好友申请通知'
            total = packet.get('total')
            if content and device_token :
                message = Message(tokens=[device_token], alert=content, badge=int(total), content_available=1, my_extra=15)
                srv = APNs(con)
                res = srv.send(message)

                # Check failures. Check codes in APNs reference docs.
                for token, reason in res.failed.items():
                    code, errmsg = reason
                    logger.info("Device faled: {0}, reason: {1}".format(token, errmsg))

            # Check failures not related to devices.
            for code, errmsg in res.errors:
                logger.error("Error: %s" % errmsg)


class emsg_auth(BaseService):
    def auth(self,body):
        '''
        用户登陆时,emsg 会回调此方法
        '''
        sn,userid,token = '','',''
        try:
            sn = body.get('sn')
            userid = body['params']['uid']
            token = body['params']['token']
            tokenPo = UserToken.objects.get(id=token)
            if tokenPo.userid == userid :
                logger.info('[emsg_auth.auth success] sn=%s , userid=%s , token=%s' % (sn,userid,token))
                return self._success(sn=sn,success=True)
            else:
                logger.info('[emsg_auth.auth fail] sn=%s , token=%s , userid=%s' % (sn,userid,token))
                return self._success(sn=sn,success=False,code='2000',reason=errors.error_2000)
        except:
            logger.info('[emsg_auth.auth error] sn=%s , token=%s , userid=%s' % (sn,userid,token))
            logger.error(traceback.format_exc())
            return self._success(sn=sn,success=False,code='2000',reason=errors.error_2000)


