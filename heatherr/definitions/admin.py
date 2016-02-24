from django.contrib import admin

from heatherr.definitions.models import Acronym


class AcronymModelAdmin(admin.ModelAdmin):
    pass


admin.site.register(Acronym, AcronymModelAdmin)
