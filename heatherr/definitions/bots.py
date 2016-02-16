import json

from heatherr.views import dispatcher
from heatherr.models import SlackAccount
from heatherr.definitions.models import Acronym


definitions = dispatcher.bot('definitions')


@definitions.ambient(r'@BOTUSERID: (?P<acronym>[A-Z]+) is (?P<definition>.+)$')
def add_defintion(bot_user_id, bot_user_name, message, match):
    slackaccount = SlackAccount.objects.get(bot_user_id=bot_user_id)
    data = match.groupdict()
    Acronym.objects.get_or_create(slackaccount=slackaccount,
                                  acronym=data['acronym'],
                                  definition=data['definition'])
    slackaccount.api_call(
        'reactions.add',
        name='thumbsup',
        channel=message['channel'],
        timestamp=str(message['ts']),)


@definitions.ambient(r'@BOTUSERID: (?P<acronym>[A-Z]+)\?',
                     r'@BOTUSERID: what is (?P<acronym>[A-Z]+)\??',
                     r'@BOTUSERID: what does (?P<acronym>[A-Z]+) mean\??')
def get_definition(bot_user_id, bot_user_name, message, match):
    slackaccount = SlackAccount.objects.get(bot_user_id=bot_user_id)
    data = match.groupdict()
    acronyms = Acronym.objects.filter(slackaccount=slackaccount,
                                      acronym__icontains=data['acronym'])
    if not acronyms.exists():
        return message.reply('I don\'t have any definitions for %s.' % (
            data['acronym'],))

    slackaccount.api_call(
        'chat.postMessage',
        channel=message['channel'],
        text='Definitions for *%s*' % data['acronym'],
        pretext='Type `<@%s> remove <number> for %s` to remove defintions' % (
            bot_user_id, data['acronym'],),
        attachments=json.dumps([{
            'text': '\n'.join([
                '%s (%s)' % (acronym.definition, acronym.pk)
                for acronym in acronyms
            ])
        }])
    )


@definitions.ambient(r'@BOTUSERID: remove (?P<pk>\d+) for (?P<acronym>[A-Z]+)$')  # noqa
def remove_definition(bot_user_id, bot_user_name, message, match):
    slackaccount = SlackAccount.objects.get(bot_user_id=bot_user_id)
    data = match.groupdict()
    deleted_rows, _ = Acronym.objects.filter(
        slackaccount=slackaccount,
        pk=data['pk'],
        acronym=data['acronym']).delete()
    if deleted_rows:
        return message.reply('Deleted %(pk)s for %(acronym)s.' % data)
    return message.reply('Sorry, don\'t know what to delete.')
