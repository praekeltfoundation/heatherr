from heatherr.views import dispatcher


bot = dispatcher.bot('bots name')
# direct_mention = dispatcher.direct_mention()
# mention = dispatcher.mention()
# direct_message = dispatcher.direct_message()


@bot.ambient(r'(thanks|thank you|thx|tx)\s*@?(?P<name>[\w.-]+)',
             r'@?(?P<name>[\w.-]+):\s*(thanks|thank you|thx|tx)!?$')
def thankyou(message, match):
    data = match.groupdict()
    print message.bot_access_token
    message.reply('you thanked: %(name)s' % data)

@bot.ambient(r'(.+$)')
def everything(message, match):
    (content,) = match.groups()
    message.reply('you said: %s' % (content,))
