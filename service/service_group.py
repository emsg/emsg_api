# /usr/bin/env python
# coding=utf8
import json
import logging
import datetime
import traceback
import string
import uuid
import emsg_simple_api.emsg_client as emsg_client
import emsg_simple_api.poster as poster

from emsg_simple_api.settings import EMSG_RPC,EMSG_ACCESS_TOKEN
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
                gid = group.id
                # push
                self._push_notify(from_jid=self._jid(uid),gid=gid,action="create")
                return self._success(sn=sn, success=True, entity=dict( gid=gid ))
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
                sn,token,params = self._get_sn_token_params(body)
                auth_user,_ = self._get_user_by_token(token)
                uid = auth_user.id
                gid = params['gid']
                users = list(params['users'])
                logger.debug("%s,%s,%s" % (sn,gid,users))
                now = int(time.time())
                group = Group.objects.get(id=gid)
                group.et = now
                us = group.users
                if us :
                    all = us.split(',')[1:-1]
                else :
                    all = []
                # 取交集，然后在合并后的列表中
                # 如果存在交集，那就是重复的添加，需要将交叉的数据删掉在 users 列表中
                for d in set(all).intersection(set(users)):
                    logger.debug("already_added group=%s , uid=%s" % (gid,d))
                    users.remove(d)
                if not users :
                    return self._success(sn=sn, success=False, code='1007', reason=errors.error_1007_1)

                all = list(set(all + users))
                group.users = ","+string.join(all,",")+","
                group.save()
                # TODO reload group user, call sara rpc
                rpc_result = self._call_reload_rpc(gid)
                logger.debug(rpc_result)
                # push
                self._push_notify(from_jid=self._jid(uid),gid=gid,action="add",members=users)
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
                # push, 退出时要先推送，后刷新成员，否则消息服务器不受理此条推送
                self._push_notify(from_jid=self._jid(uid),gid=gid,action="del")

                user_list = users.split(',')[1:-1]
                user_list.remove(uid)
                group.users = ","+string.join(user_list,',')+","
                group.save()
                # reload group user, call sara rpc
                rpc_result = self._call_reload_rpc(gid)
                logger.debug(rpc_result)
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

    def _call_reload_rpc(self,gid):
        body = {
            "sn": uuid.uuid4().hex,
            "token":EMSG_ACCESS_TOKEN,
            "service": "emsg_group",
            "method": "reload",
            "params": {
                "gid":str(gid),
                "domain":self._domain()
            }
        }
        jbody = json.dumps(body)
        form = {"body":jbody}
        return poster.submit(EMSG_RPC,form)

    def _push_notify(self,from_jid,gid,action,members=[]):
        '''
        推送群事件
        :param from_jid: 发送人jid
        :param gid: 群id
        :param action: 事件名称包括 create / add / del
        :return:
        '''
        packet = {
            "envelope": {
                "id": uuid.uuid4().hex,
                "type": 2,
                "gid": str(gid),
                "from": from_jid,
                "ack": 1
            },
            "payload": {
                "attrs": {
                    "message_type": "notify",
                    "action": action
                }
            }
        }
        if members :
            packet['payload']['attrs']['members'] = members
        packet_str = json.dumps(packet)
        logger.info("group_push_notify = %s" % packet_str)
        emsg_client.process(packet_str)


