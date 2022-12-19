from django.contrib import admin

from .models import *
# Register your models here.
admin.site.register(Department)
admin.site.register(Section)
admin.site.register(Schedule)
admin.site.register(Comment)
admin.site.register(FriendRequest)
admin.site.register(Friends)
admin.site.register(Profile)

