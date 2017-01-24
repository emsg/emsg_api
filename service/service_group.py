# /usr/bin/env python
# coding=utf8
import json
import logging
import datetime
import traceback
import string
import uuid
import emsg_simple_api.emsg_client as emsg_client

import django.utils.timezone as dtz
from django.contrib.auth.models import User
from django.db import transaction
import errors
from models import *

from service import BaseService,token

logger = logging.getLogger(__name__)
from django.forms.models import model_to_dict

class group(BaseService):
    '''
    简单群模块：
    https://github.com/emsg/emsg_simple_api/wiki/GroupService
    '''
    @token
    def create(self, body):
        '''
        1 创建群聊
        '''
        try:
            with transaction.atomic():
                sn,token,params = self._get_sn_token_params(body)
                auth_user,_ = self._get_user_by_token(token)
                uid = auth_user.id
                name = params.get('name')
                comment = params.get('comment')
                users = params.get('users')
                logger.debug("%s,%s,%s,%s,%s" % (sn,name,comment,users,uid))
                now = int(time.time())
                group = Group()
                group.ct = now
                group.et = now
                group.name = name
                group.comment = comment
                if users and len(users)>0 :
                    users.append(str(uid))
                    users = list(set(users))
                    group.users = ","+string.join(users,",")+","
                group.save()
                return self._success(sn=sn, success=True, entity=dict( gid=group.id ))
        except:
            logger.error(traceback.format_exc())
            return self._success(sn=sn, success=False, code='1000', reason=errors.error_1000)
    @token
    def add(self, body):
        '''
        2 添加成员
        '''
        try:
            with transaction.atomic():
                sn = body.get('sn')
                gid = body['params']['gid']
                users = body['params']['users']
                logger.debug("%s,%s,%s" % (sn,gid,users))
                now = int(time.time())
                group = Group.objects.get(id=gid)
                group.et = now
                us = group.users
                if us :
                    all = us.split(',')[1:-1]
                else :
                    all = []
                all = list(set(all + users))
                group.users = ","+string.join(all,",")+","
                group.save()
                return self._success(sn=sn, success=True, entity=dict( users=all))
        except:
            logger.error(traceback.format_exc())
            return self._success(sn=sn, success=False, code='1000', reason=errors.error_1000)

    @token
    def get_user_list(self, body):
        '''
        3 获取成员
        '''
        try:
            sn = body.get('sn')
            gid = body['params']['gid']
            logger.debug("%s,%s" % (sn,gid))
            group = Group.objects.get(id=gid)
            us = group.users
            if us :
                all = us.split(',')[1:-1]
            else :
                all = []
            return self._success(sn=sn, success=True, entity=dict( users=all))
        except:
            logger.error(traceback.format_exc())
            return self._success(sn=sn, success=False, code='1008', reason=errors.error_1008)

    @token
    def unsubscribe(self,body):
        '''
        4 退出群
        '''
        try:
            sn, token, params = self._get_sn_token_params(body)
            auth_user,_ = self._get_user_by_token(token)
            gid = params['gid']
            uid = auth_user.id
            group = Group.objects.get(id=gid)
            users = group.users
            if users and uid:
                user_list = users.split(',')[1:-1]
                user_list.remove(uid)
                group.users = ","+string.join(user_list,',')+","
                group.save()
            return self._success(sn=sn, success=True)
        except:
            logger.error(traceback.format_exc())
            return self._success(sn=sn, success=False, code='1000', reason=errors.error_1000)
    @token
    def get_my_group(self,body):
        '''
        5 获取我参与的群
        '''
        try:
            sn, token, _ = self._get_sn_token_params(body)
            auth_user,_ = self._get_user_by_token(token)
            uid = auth_user.id
            pos = Group.objects.filter(users__contains=','+str(uid)+',')
            groups = []
            for g in pos:
                ul = g.users.split(',')
                if ul and len(ul)>2 :
                    ul = ul[1:-1]
                else:
                    ul = []
                vo = dict(
                    gid = g.id,
                    icon = [],
                    name = g.name,
                    comment = g.comment,
                    users = ul
                )
                groups.append(vo)
            return self._success(sn=sn, success=True,entity=dict(groups=groups))
        except:
            logger.error(traceback.format_exc())
            return self._success(sn=sn, success=False, code='1000', reason=errors.error_1000)



