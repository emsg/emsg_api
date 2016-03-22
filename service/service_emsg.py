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
'''
emsg_server 回调接口文档
https://github.com/cc14514/emsg_sdk/wiki/emsg_server-%E6%8E%A5%E5%8F%A3%E6%96%87%E6%A1%A3
'''

class user_message(BaseService):
    def offline(self,body):
        '''
        离线消息回调,其中 params 是 packet
        :param body:
        :return:
        '''
        sn = body['sn']
        packet = body['params']
        logger.info('[emsg_offline] packet = %s' % packet)
        return self._success(sn=sn,success=True)

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
                logger.info('[emsg_auth.auth success] sn=%s , token=%s , userid=%s' % (sn,userid,token))
                return self._success(sn=sn,success=True)
            else:
                logger.info('[emsg_auth.auth fail] sn=%s , token=%s , userid=%s' % (sn,userid,token))
                return self._success(sn=sn,success=False,code='2000',reason=errors.error_2000)
        except:
            logger.info('[emsg_auth.auth error] sn=%s , token=%s , userid=%s' % (sn,userid,token))
            logger.error(traceback.format_exc())
            return self._success(sn=sn,success=False,code='2000',reason=errors.error_2000)


