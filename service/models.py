# /usr/bin/env python
# coding=utf8
from __future__ import unicode_literals
import time
from django.db import models

class UserInfo(models.Model):
    nickname = models.CharField(max_length=200L,blank=True,null=True)
    gender = models.CharField(max_length=10L,blank=True,null=True)
    birthday = models.CharField(max_length=100L,blank=True,null=True)
    icon = models.CharField(max_length=1000L,blank=True,null=True)
    geo = models.CharField(max_length=1000L,blank=True,null=True)
    class Meta:
        db_table='user_info'

class EmsgServer(models.Model):
    host = models.CharField(max_length=200L,blank=True)
    port = models.CharField(max_length=100L,blank=True)
    domain = models.CharField(max_length=100L,blank=True)
    licence = models.CharField(max_length=200L,blank=True)
    class Meta:
        db_table='emsg_server'

class UserToken(models.Model):
    id = models.CharField(max_length=64L,primary_key=True)
    userid = models.IntegerField()
    ct = models.IntegerField()
    class Meta:
        db_table='user_token'


class UserContact(models.Model):
    '''
    联系人信息
    '''
    userid = models.IntegerField()
    contactid = models.IntegerField()
    dnd = models.IntegerField(default=1)
    status = models.CharField(max_length=50L,blank=True,default='add')
    ct = models.IntegerField(default=int(time.time()))
    et = models.IntegerField(default=int(time.time()))
    class Meta:
        db_table='user_contact'

