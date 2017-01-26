# /usr/bin/env python
# coding=utf8
from __future__ import unicode_literals
import time
from django.db import models
import json

class UserInfo(models.Model):
    nickname = models.CharField(max_length=200L,blank=True,null=True)
    gender = models.CharField(max_length=10L,blank=True,null=True)
    birthday = models.CharField(max_length=100L,blank=True,null=True)
    icon = models.CharField(max_length=1000L,blank=True,null=True)
    geo = models.CharField(max_length=1000L,blank=True,null=True)
    device_token = models.CharField(max_length=200L,blank=True,null=True)
    def __str__(self): return toString(self)
    class Meta:
        verbose_name = '用户扩展信息'
        db_table='user_info'

class EmsgServer(models.Model):
    host = models.CharField(max_length=200L,blank=True)
    port = models.CharField(max_length=100L,blank=True)
    domain = models.CharField(max_length=100L,blank=True)
    licence = models.CharField(max_length=200L,blank=True)

    def __str__(self): return toString(self)
    class Meta:
        verbose_name = '消息服务器'
        db_table='emsg_server'

class UserToken(models.Model):
    id = models.CharField(max_length=64L,primary_key=True)
    userid = models.IntegerField()
    ct = models.IntegerField()
    def __str__(self): return toString(self)
    class Meta:
        verbose_name = '用户Token'
        db_table='user_token'


class UserContact(models.Model):
    '''
    联系人信息
    '''
    userid = models.IntegerField()
    contactid = models.IntegerField()
    dnd = models.IntegerField(default=1)
    status = models.CharField(max_length=50L,blank=True,default='add')
    ct = models.IntegerField()
    et = models.IntegerField()
    def __str__(self): return toString(self)
    class Meta:
        verbose_name = '联系人'
        db_table='user_contact'

class Group(models.Model):
    '''
    简单群
    '''
    icon = models.CharField(max_length=4000L,blank=True)
    name = models.CharField(max_length=500L,blank=True)
    comment = models.CharField(max_length=2000L,blank=True)
    users = models.CharField(max_length=4000L,blank=True)
    ct = models.IntegerField()
    et = models.IntegerField()
    def __str__(self): return toString(self)
    class Meta:
        verbose_name = '简单群组'
        db_table='simple_group'



def toString(obj):
    d = obj.__dict__
    del d['_state']
    str = ''
    for k,v in d.items() :
        str = str + (' ( %s=%s ) ; ' % (k,v))
    return str
