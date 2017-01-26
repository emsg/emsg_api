from django.contrib import admin

from models import *

@admin.register(UserInfo,EmsgServer,UserToken,UserContact,Group)
class UserInfoAdmin(admin.ModelAdmin):
    #list_display = ('nickname','gender','birthday',)
    #search_fields = ('nickname',)
    pass

