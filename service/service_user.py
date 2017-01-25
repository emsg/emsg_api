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
import pysolr

from emsg_simple_api.settings import EMSGUSER_SOLR_RPC
from service import BaseService,token

logger = logging.getLogger(__name__)
from django.forms.models import model_to_dict

emsguser_solr = pysolr.Solr(url=EMSGUSER_SOLR_RPC)

class user(BaseService):
    '''
    用户模块
    https://github.com/emsg/emsg_simple_api/wiki/UserService
    '''

    def register(self, body):
        '''
        1 用户注册
        '''
        try:
            with transaction.atomic():
                sn = body.get('sn')
                username = body['params']['username']
                password = body['params']['password']
                nickname = body['params']['nickname']
                email = body['params']['email']
                gender = body['params']['gender']
                geo = body['params'].get('geo')  # 坐标
                device_token = body['params'].get('device_token')  # ios 设备 id
                birthday = body['params']['birthday']
                # 如果能取到,则不可以再注册了,就是注册过了
                # 用户名和邮箱不能重复
                try:
                    User.objects.get(username=username)
                    return self._success(sn=sn, success=False, code='1001_1', reason=errors.error_1001_1)
                except:
                    logger.debug('该用户名合法 %s' % username)
                try:
                    User.objects.get(email=email)
                    return self._success(sn=sn, success=False, code='1001_2', reason=errors.error_1001_2)
                except:
                    logger.debug('该邮箱名合法 %s' % email)
                now = dtz.now()
                user = User()
                user.username = username
                user.email = email
                user.is_staff = False
                user.is_superuser = False
                user.is_active = True
                user.set_password(password)
                user.date_joined = now
                user.last_login = now
                user.save()
                logger.debug('create_auth_user ==> %s' % user.__dict__)

                user_info = UserInfo(id=user.id)
                user_info.nickname = nickname
                user_info.gender = gender
                user_info.geo = geo
                user_info.device_token = device_token
                user_info.birthday = birthday
                user_info.save()
                logger.debug('create_user_info ==> %s' % user.__dict__)

                user_map = self._get_user_map(auth_user=user, user_info=user_info)
                logger.debug('user_map ==> %s' % user_map)
                user_token = self._gen_token(user_info.id)

                return self._success(sn=sn, success=True, entity=dict(
                    token=user_token.id,
                    user=user_map,
                    emsg_server=self._get_emsg_server()
                ))
        except:
            logger.error(traceback.format_exc())
            return self._success(sn=sn, success=False, code='1000', reason=errors.error_1000)

    def login(self, body):
        '''
        2 用户登陆
        '''
        sn = body.get('sn')
        username = body['params']['username']
        password = body['params']['password']
        device_token = body['params'].get('device_token')
        u = User.objects.get(username=username)
        if u.check_password(password):
            user_token = self._gen_token(u.id)
            user_map = self._get_user_map(id=u.id)
            if device_token :
                user_info = UserInfo.objects.get(id=u.id)
                user_info.device_token = device_token
                user_info.save()
            return self._success(sn=sn, success=True, entity=dict(
                token=user_token.id,
                user=user_map,
                emsg_server=self._get_emsg_server()
            ))
        else:
            return self._success(sn=sn, success=False, code='1002', reason=errors.error_1002)

    @token
    def get_user_info(self, body):
        '''
        3 获取用户信息
        '''
        sn, token, params = self._get_sn_token_params(body)
        user_map = {}
        if params and params.has_key('userid'):
            userid = params.get('userid')
            user_map = self._get_user_map(id=userid)
        else:
            user_map = self._get_user_map(token=token)
        if user_map:
            return self._success(sn=sn, success=True, entity=dict(
                user=user_map,
            ))
        else:
            return self._success(sn=sn, success=False, code='1003', reason=errors.error_1003)

    @token
    def update_user_info(self, body):
        '''
        4 修改用户信息
        '''
        sn, token, params = self._get_sn_token_params(body)
        try:
            with transaction.atomic():
                auth_user, user_info = self._get_user_by_token(token)
                email = params.get('email')
                if email and email != auth_user.email:
                    try:
                        User.objects.get(email=email)
                        return self._success(sn=sn, success=False, code='1001_2', reason=errors.error_1001_2)
                    except:
                        auth_user.email = email
                        auth_user.save()
                nickname = params.get('nickname')
                gender = params.get('gender')
                birthday = params.get('birthday')
                if nickname: user_info.nickname = nickname
                if gender: user_info.gender = gender
                if birthday: user_info.birthday = birthday
                user_info.save()
                return self._success(sn=sn, success=True)
        except Exception as e:
            logger.error(e)
            logger.error(traceback.format_exc())
            return self._success(sn=sn, success=False, code='1004', reason=errors.error_1004)

    @token
    def set_icon(self, body):
        '''
        5 修改用户头像
        '''
        sn, token, params = self._get_sn_token_params(body)
        icon = params.get('icon_url')
        auth_user, user_info = self._get_user_by_token(token)
        user_info.icon = icon
        user_info.save()
        return self._success(sn=sn, success=True)

    @token
    def update_password(self, body):
        '''
        6 修改密码
        '''
        try:
            sn, token, params = self._get_sn_token_params(body)
            auth_user, user_info = self._get_user_by_token(token)
            old_password = params.get('old_password')
            new_password = params.get('new_password')
            if old_password and new_password:
                if auth_user.check_password(old_password):
                    auth_user.set_password(new_password)
                    auth_user.save()
                    return self._success(sn=sn, success=True)
                else:
                    return self._success(sn=sn, success=False, code='1006', reason=errors.error_1006_2)
            else:
                return self._success(sn=sn, success=False, code='1006', reason=errors.error_1006_1)
        except Exception as e:
            logger.error(e)
            logger.error(traceback.format_exc())
            return self._success(sn=sn, success=False, code='1006', reason=errors.error_1006_3)

    @token
    def contact(self, body):
        '''
        7 联系人接口
        "action":"add\reject\accept\list"
        :param body:
        :return:
        '''
        try:
            sn, token, params = self._get_sn_token_params(body)
            action = params.get('action')
            if 'add' == action : # 添加好友
                return self._add_contact(body)
            elif 'reject' == action :# 拒绝
                return self._reject_contact(body)
            elif 'accept' == action :# 接受
                return self._accept_contact(body)
            elif 'delete' == action :# 删除
                return self._delete_contact(body)
            elif 'list' == action :# 好友列表
                return self._list_contact(body)
            else :
                return self._success(sn=sn, success=False, code='1007', reason=errors.error_1007_3)
            return self._success(sn=sn, success=True)
        except Exception as e:
            logger.error(e)
            logger.error(traceback.format_exc())
            return self._success(sn=sn, success=False, code='1007', reason=errors.error_1007)

    @token
    def find_user(self, body):
        '''
        8 查找用户
        目前只支持昵称查找
        :param body:
        :return:
        '''
        try:
            sn, token, params = self._get_sn_token_params(body)
            current_user_map = self._get_user_map(token=token)
            email = params.get('email')
            nickname = params.get('nickname')
            user_list = []
            if email :
                for auth_user in User.objects.filter(email__contains=email):
                    user_map = self._get_user_map(id=auth_user.id)
                    user_map['is_contact'] = self._is_contact(userid=current_user_map['id'],contactid=auth_user.id)
                    user_list.append(user_map)
            elif nickname :
                for user_info in UserInfo.objects.filter(nickname__contains=nickname):
                    user_map = self._get_user_map(id=user_info.id)
                    user_map['is_contact'] = self._is_contact(userid=current_user_map['id'],contactid=user_info.id)
                    user_list.append(user_map)
            return self._success(sn=sn, success=True,entity={'user_list':user_list})
        except Exception as e:
            logger.error(e)
            logger.error(traceback.format_exc())
            return self._success(sn=sn, success=False, code='1008', reason=errors.error_1008)

    @token
    def logout(self,body):
        '''
        9 退出登陆
        '''
        sn,token,params = self._get_sn_token_params(body)
        try:
            with transaction.atomic():
                user_token = UserToken.objects.get(id=token)
                userid = user_token.userid
                user_info = UserInfo.objects.get(id=userid)
                user_info.device_token = ''
                user_info.save()
                user_token.delete()
        except :
            pass
        return self._success(sn=sn, success=True)

    @token
    def set_geo(self,body):
        '''
        输入参数
        {
          "sn": "sn_10",
          "service": "user",
          "method": "set_geo",
          "token":"用户身份标示",
          "params": {
            "geo":"坐标格式: lat,lng"
          }
        }

        &q=*:*&fq={!geofilt}&sfield=store&pt=45.15,-93.85&d=50&sort=geodist() asc
        '''
        sn, token, params = self._get_sn_token_params(body)
        try:
            auth_user, user_info = self._get_user_by_token(token)
            userid = user_info.id
            nickname = user_info.nickname
            gender = user_info.gender
            icon = user_info.icon
            geo = params.get('geo')
            user_info.geo = geo
            user_info.save()
            emsguser_solr.add(docs=[dict(
                id = userid,
                nickname_s = nickname,
                gender_s = gender,
                geo_p = geo,
                icon_s = icon,
                ts_i = int(time.time()),
                last_time_s = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )])
        except :
            err = traceback.format_exc()
            logger.error(err)
            return self._success(sn=sn, success=False, code='1010', reason=err)
        return self._success(sn=sn, success=True)

    @token
    def find_user_by_geo(self,body):
        '''
        {
          "sn": "sn_11",
          "service": "user",
          "method": "find_user_by_geo",
          "token":"用户身份标示",
          "params": {
            "geo":"坐标格式: lat,lng",
            "gender":"性别：男／女，如果传空则忽略此条件",
            "page_size":"每页几条，默认20",
            "page_no":"第几页，从0开始"
          }
        }
        '''
        # 先同步一次坐标
        self.set_geo(body)

        sn, token, params = self._get_sn_token_params(body)
        try:
            geo = params.get('geo')
            page_size = params.get('page_size')
            page_no = params.get('page_no')
            gender = params.get('gender')
            if not page_size : page_size = 20
            if not page_no : page_no = 0
            if gender :
                q = "gender_s:%s" % gender
            else :
                q = "*:*"
            result = emsguser_solr.search(
                q, fq="{!geofilt}", sfield="geo_p", d="500", sort="geodist() asc", fl="*,_dist_:geodist()",
                pt=geo,
                start= int(page_no)*int(page_size),
                rows=page_size
            )
            total_count = result.hits
            user_list = []
            if total_count:
                for row in result.docs :
                    u = dict(
                        id=row.get('id'),
                        nickname = row.get('nickname_s'),
                        gender = row.get('gender_s'),
                        icon = row.get('icon_s'),
                        last_time = row.get('last_time_s'),
                        ts = row.get('ts_i'),
                        dist = row.get('_dist_'),
                    )
                    user_list.append(u)

            return self._success(sn=sn, success=True,entity=dict(
                page_size = page_size,
                page_no = page_no,
                total_count = total_count,
                user_list = user_list
            ))
        except:
            err = traceback.format_exc()
            logger.error(err)
            return self._success(sn=sn, success=False, code='1011', reason=err)

    ########################################
    ## private
    ########################################
    def _list_contact(self,body):
        '''
        好友列表
        :param body:
        :return:
        '''
        sn, token, params = self._get_sn_token_params(body)
        auth_user, user_info = self._get_user_by_token(token)
        userid = auth_user.id
        contacts = []
        for contact in UserContact.objects.filter(userid=userid ):
            if 'accept' == contact.status:
                user_map = self._get_user_map(id=contact.contactid)
                contacts.append(user_map)
        return self._success(sn=sn, success=True,entity={'contacts':contacts})

    def _delete_contact(self,body):
        '''
        删除联系人
        :param body:
        :return:
        '''
        try:
            sn, token, params = self._get_sn_token_params(body)
            auth_user, user_info = self._get_user_by_token(token)
            userid = auth_user.id
            contact_id = params.get('contact_id')
            with transaction.atomic():
                for contact in UserContact.objects.filter(userid=contact_id, contactid=userid):
                    contact.delete()
                for user_contact in UserContact.objects.filter(userid=userid,contactid=contact_id) :
                    user_contact.delete()
                packet = {
                    "envelope": {
                        "id": uuid.uuid4().hex,
                        "type": 1,
                        "from": self._jid(userid),
                        "to": self._jid(contact_id),
                        "ack": 1
                    },
                    "vsn": "0.0.1",
                    "payload": {
                        "attrs": {
                            "action": "delete",
                            "message_type": "contact",
                            "contact_id": str(userid),

                            "messageType": "contact",
                            "contactId": str(userid),
                        }
                    }
                }
                packet_str = json.dumps(packet)
                logger.info("delete_contact_packet = %s" % packet_str)
                emsg_client.process(packet_str)
        except Exception as e :
            logger.error(e)
            logger.error(traceback.format_exc())
            return self._success(sn=sn, success=False, code='1007', reason=errors.error_1007)
        return self._success(sn=sn, success=True)

    def _accept_contact(self,body):
        '''
        接受添加好友请求
        :param body:
        :return:
        '''
        try:
            sn, token, params = self._get_sn_token_params(body)
            auth_user, user_info = self._get_user_by_token(token)
            userid = auth_user.id
            contact_id = params.get('contact_id')
            with transaction.atomic():
                # 将对方添加我为好友的数据状态改为 拒绝
                for contact in UserContact.objects.filter(userid=contact_id, contactid=userid):
                    contact.status = 'accept'
                    contact.et = int(time.time())
                    contact.save()
                # 在数据库中创建联系人记录
                # 清理数据,重复接受时产生垃圾数据
                for user_contact in UserContact.objects.filter(userid=userid,contactid=contact_id) :
                    user_contact.delete()
                user_contact = UserContact()
                user_contact.userid = userid
                user_contact.contactid = contact_id
                user_contact.status = 'accept'
                user_contact.save()

                packet = {
                    "envelope": {
                        "id": uuid.uuid4().hex,
                        "type": 1,
                        "from": self._jid(userid),
                        "to": self._jid(contact_id),
                        "ack": 1
                    },
                    "vsn": "0.0.1",
                    "payload": {
                        "attrs": {
                            "action": "accept",
                            "message_type": "contact",
                            "contact_icon": user_info.icon,
                            "contact_nickname": user_info.nickname,
                            "contact_id": str(userid),

                            "messageType": "contact",
                            "contactIcon": user_info.icon,
                            "contactNickname": user_info.nickname,
                            "contactId": str(userid)
                        }
                    }
                }
                packet_str = json.dumps(packet)
                logger.info("accept_contact_packet = %s" % packet_str)
                emsg_client.process(packet_str)
            return self._success(sn=sn, success=True)
        except Exception as e:
            logger.error(e)
            logger.error(traceback.format_exc())
            return self._success(sn=sn, success=False, code='1007', reason=errors.error_1007)

    def _reject_contact(self,body):
        '''
        拒绝添加好友请求
        :param body:
        :return:
        '''
        try:
            sn, token, params = self._get_sn_token_params(body)
            auth_user, user_info = self._get_user_by_token(token)
            userid = auth_user.id
            contact_id = params.get('contact_id')
            with transaction.atomic():
                # 将对方添加我为好友的数据状态改为 拒绝
                for contact in UserContact.objects.filter(userid=contact_id, contactid=userid):
                    contact.status = 'reject'
                    contact.et = int(time.time())
                    contact.save()
                packet = {
                    "envelope": {
                        "id": uuid.uuid4().hex,
                        "type": 1,
                        "from": self._jid(userid),
                        "to": self._jid(contact_id),
                        "ack": 1
                    },
                    "vsn": "0.0.1",
                    "payload": {
                        "attrs": {
                            "action": "reject",
                            "message_type": "contact",
                            "contact_icon": user_info.icon,
                            "contact_nickname": user_info.nickname,
                            "contact_id": str(userid),

                            "messageType": "contact",
                            "contactIcon": user_info.icon,
                            "contactNickname": user_info.nickname,
                            "contactId": str(userid)
                        }
                    }
                }

                packet_str = json.dumps(packet)
                logger.info("reject_contact_packet = %s" % packet_str)
                emsg_client.process(packet_str)
            return self._success(sn=sn, success=True)
        except Exception as e:
            logger.error(e)
            logger.error(traceback.format_exc())
            return self._success(sn=sn, success=False, code='1007', reason=errors.error_1007)

    def _add_contact(self,body):
        '''
        添加好友
        :param body:
        :return:
        '''
        try:
            sn, token, params = self._get_sn_token_params(body)
            auth_user, user_info = self._get_user_by_token(token)
            userid = auth_user.id
            contact_id = params.get('contact_id')
            with transaction.atomic():
                for contact in UserContact.objects.filter(userid=userid, contactid=contact_id):
                    if 'accept' == contact.status:
                        # 已添加,不能重复添加
                        return self._success(sn=sn, success=False, code='1007', reason=errors.error_1007_1)
                    else :
                        # 如果拒绝过,或者正在等待对方应答,则删除这个记录,重新添加
                        contact.delete()

                # 在数据库中创建联系人记录
                user_contact = UserContact()
                user_contact.userid = userid
                user_contact.status = 'add'
                user_contact.contactid = contact_id
                user_contact.save()
                # 并且判断对方是否添加过自己,如果没有添加过,则发加好友推送
                if not UserContact.objects.filter(userid=contact_id, contactid=userid):
                    # 对方没有加过我,需要推送
                    packet = {
                        "envelope": {
                            "id": uuid.uuid4().hex,
                            "type": 1,
                            "from": self._jid(userid),
                            "to": self._jid(contact_id),
                            "ack": 1
                        },
                        "vsn": "0.0.1",
                        "payload": {
                            "attrs": {
                                "action": "add",
                                # TODO 为了兼容一个错误的命名，稍后修改
                                "message_type": "contact",
                                "contact_icon": user_info.icon,
                                "contact_nickname": user_info.nickname,
                                "contact_id": str(userid),
                                # -------------------------------------
                                "messageType": "contact",
                                "contactIcon": user_info.icon,
                                "contactNickname": user_info.nickname,
                                "contactId": str(userid)
                            }
                        }
                    }
                    packet_str = json.dumps(packet)
                    logger.info("add_contact_packet = %s" % packet_str)
                    emsg_client.process(packet_str)
            return self._success(sn=sn, success=True)
        except Exception as e:
            logger.error(e)
            logger.error(traceback.format_exc())
            return self._success(sn=sn, success=False, code='1007', reason=errors.error_1007_2)

    def _get_user_map(self, id=None, auth_user=None, user_info=None, token=None):
        '''
        根据传入的参数不同,用不同的方式去拼凑 user 字典
        包含 auth_user 和 user_info 两张表的信息,其中日期可以处理掉,转成时间戳
        :param id: 如果有id则从数据库取,否则用另外两个对象来拼
        :param auth_user:
        :param user_info:
        :param token:
        :return:
        '''
        if id:
            auth_user = User.objects.get(id=id)
            user_info = UserInfo.objects.get(id=id)
        elif token:
            auth_user, user_info = self._get_user_by_token(token)
            # tokenPo = UserToken.objects.get(id=token)
            # userid = tokenPo.userid
            # auth_user = User.objects.get(id=userid)
            # user_info = UserInfo.objects.get(id=userid)
        elif auth_user == None or user_info == None:
            raise Exception("notfound")
        d1 = model_to_dict(user_info)
        d2 = dict(username=auth_user.username, email=auth_user.email)
        d1.update(d2)
        return d1

    def _get_emsg_server(self):
        el = EmsgServer.objects.all()
        if el:
            e = el[0]
            e.licence = ''
            d = model_to_dict(e)
            del d['id']
            return d
        else:
            return {}

    def _is_contact(self,userid,contactid):
        '''
        是否为好友
        :param userid:
        :param contactid:
        :return: True / False
        '''
        for contact in UserContact.objects.filter(userid=userid,contactid=contactid,status='accept'):
            return True
        return False

    def _gen_token(self, userid):
        user_token = UserToken()
        user_token.id = uuid.uuid4().hex
        user_token.userid = userid
        user_token.ct = int(time.time())
        user_token.save()
        return user_token

