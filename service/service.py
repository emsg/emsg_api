# /usr/bin/env python
# coding=utf8
import json
import logging
import datetime
import traceback
import uuid
import emsg_simple_api.emsg_client as emsg_client

import django.utils.timezone as dtz
from django.contrib.auth.models import User
from django.db import transaction
import errors
from models import *
logger = logging.getLogger(__name__)

def token(x):
    '''
    校验 token 是否有效
    :param x:
    :return:
    '''

    def f(*args):
        sn, token = '', ''
        for p in args:
            if type(p) == dict:
                sn = p.get('sn')
                token = p.get('token')
        if token:
            try:
                UserToken.objects.get(id=token)
                return x(*args)
            except:
                return BaseService()._success(sn=sn, success=False, code='2000', reason=errors.error_2000)
        else:
            return BaseService()._success(sn=sn, success=False, code='2000', reason=errors.error_2000)

    return f


class BaseService(object):
    def _success(self, sn, success=True, entity={}, code='', reason=''):
        if success:
            return dict(sn=sn, success=success, entity=entity)
        else:
            return dict(sn=sn, success=success, entity=dict(code=code, reason=reason))

    def _get_user_by_token(self, token):
        '''
        根据token获取用户po,包括 auth_user 和 user_info 两个对象
        :param token:
        :return:  [auth_user,user_info]
        '''
        try:
            tokenPo = UserToken.objects.get(id=token)
            userid = tokenPo.userid
            auth_user = User.objects.get(id=userid)
            user_info = UserInfo.objects.get(id=userid)
            return [auth_user, user_info]
        except Exception as e:
            raise e

    def _jid(self, userid):
        '''
        获取 jid
        :param userid:
        :return:
        '''
        es = EmsgServer.objects.all()[0]
        return '%s@%s' % (userid, es.domain)

    def _get_sn_token_params(self, body):
        sn = body.get('sn')
        token = body.get('token')
        params = body.get('params')
        return [sn, token, params]


