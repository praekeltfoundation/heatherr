from heatherr.views import dispatcher


bot = dispatcher.bot('bots name')


@bot.ambient(r'(thanks|thank you|thx|tx)\s*@?(?P<name>[\w.-]+)',
             r'@?(?P<name>[\w.-]+):\s*(thanks|thank you|thx|tx)!?$')
def thankyou(bot_user_id, bot_user_name, message, match):
    data = match.groupdict()
    return message.reply('you thanked: %(name)s' % data)
