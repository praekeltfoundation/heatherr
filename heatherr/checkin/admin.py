from django.contrib import admin

from heatherr.checkin.models import Checkin


class CheckinAdmin(admin.ModelAdmin):
    pass


admin.site.register(Checkin, CheckinAdmin)
