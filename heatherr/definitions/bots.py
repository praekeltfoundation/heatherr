import json

from heatherr.views import dispatcher
from heatherr.models import SlackAccount
from heatherr.definitions.models import Acronym


definitions = dispatcher.bot('Definitions')


@definitions.ambient(
    r'@BOTUSERID: (?P<acronym>[A-Za-z]+) is (?P<definition>.+)$')
def add_definition(bot_user_id, bot_user_name, message, match):
    """
    Teach the bot a definition:

        @BOTUSERID: UNICEF is The United Nations Children's Emergency Fund

    @BOTUSERID will respond by adding a :thumbsup: reaction to your message
    once the definition has been added.
    """
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


@definitions.ambient(r'@BOTUSERID: (?P<acronym>[A-Za-z]+)\?',
                     r'@BOTUSERID: what is (?P<acronym>[A-Za-z]+)\??',
                     r'@BOTUSERID: what does (?P<acronym>[A-Za-z]+) mean\??')
def get_definition(bot_user_id, bot_user_name, message, match):
    """
    Ask the bot for a definition

        @BOTUSERID: what does UNICEF mean?
        @BOTUSERID: what is UNICEF?
        @BOTUSERID: UNICEF?

    @BOTUSERID will respond with the definitions it knows about.
    Each definition has a unique number which one can use should it
    need to be removed.
    """
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
        as_user=True,
        text='Definitions for *%s*' % data['acronym'],
        attachments=json.dumps([{
            'pretext': ('Type `<@%s>: remove <number> for %s` '
                        'to remove definitions') % (
                            bot_user_id, data['acronym'],),
            'text': '\n'.join([
                '%s (%s)' % (acronym.definition, acronym.pk)
                for acronym in acronyms
            ])
        }])
    )


@definitions.ambient(r'@BOTUSERID: remove (?P<pk>\d+) for (?P<acronym>[A-Za-z]+)$')  # noqa
def remove_definition(bot_user_id, bot_user_name, message, match):
    """
    Remove a definition:

        @BOTUSERID: remove 1 for UNICEF

    @BOTUSERID will respond by adding a :thumbsup: reaction to your message
    once it's been removed.
    """
    slackaccount = SlackAccount.objects.get(bot_user_id=bot_user_id)
    data = match.groupdict()
    deleted_rows, _ = Acronym.objects.filter(
        slackaccount=slackaccount,
        pk=data['pk'],
        acronym=data['acronym']).delete()
    if not deleted_rows:
        return message.reply('Sorry, don\'t know what to delete.')
    slackaccount.api_call(
        'reactions.add',
        name='thumbsup',
        channel=message['channel'],
        timestamp=str(message['ts']),)
