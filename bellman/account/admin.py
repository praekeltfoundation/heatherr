from django.contrib import admin

from .models import SlackAccount


class SlackAccountAdmin(admin.ModelAdmin):
    readonly_fields = (
        'user',
        'access_token',
        'scope',
        'team_name',
        'team_id',
        'incoming_webhook_url',
        'incoming_webhook_channel',
        'incoming_webhook_configuration_url',
        'bot_user_id',
        'bot_access_token',
        'created_at',
        'updated_at',
    )

    list_display = (
        'team_name',
        'team_id',
        'created_at',
        'updated_at',
    )


admin.site.register(SlackAccount, SlackAccountAdmin)
