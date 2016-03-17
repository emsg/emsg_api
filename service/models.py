from __future__ import unicode_literals

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

