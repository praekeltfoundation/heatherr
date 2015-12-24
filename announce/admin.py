from django.contrib import admin

from announce.models import Group, Person


class GroupModelAdmin(admin.ModelAdmin):
    pass


class PersonModeladmin(admin.ModelAdmin):
    pass

admin.site.register(Group, GroupModelAdmin)
admin.site.register(Person, PersonModeladmin)
