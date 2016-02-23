.. include:: ../README.rst

Writing a Slash command
=======================

.. code:: python

    from heatherr.views import dispatcher
    from random import random

    eight_ball = dispatcher.commands('/8ball')

    @eight_ball.respond('(?P<anything>.+)')
    def fortune_teller(request, match):
        (anything,) = match.groups()
        if random() < 0.5:
            return 'All signs for `%s` point to *yes*.' % (anything,)
        return 'All signs for `%s` point to *no*.' % (anything,)

If you configure this for Slack then `/8ball will I find true love?` will
randomly return either yes or no.

Writing a Bot
=============

.. code:: python

    from heatherr.views import dispatcher
    from random import random

    bot = dispatcher.commands('Jokes')

    @bot.ambient('@BOTUSERID: joke\??')
    def knock_knock(request, match):
        return request.message.reply('I don\'t do jokes.')


`@BOTUSERID` is automatically replaced with the bot user id that's been
registered with Slack. So if your bot is called `@heatherr` then `@BOTUSERID`
will match `@heatherr`. On a low level Slack sends the `<@bot-user-id>` but
the clients display this as `@heatherr`.

`BOTUSERNAME` is also automatically replaced and that will match `heatherr`.

Timezone
~~~~~~~~

.. automodule:: heatherr.timezone.commands
    :members:

Daily or Weekly team check-ins
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: heatherr.checkin.commands
    :members:

Definitions
~~~~~~~~~~~

.. automodule:: heatherr.definitions.bots
    :members:

Group Announcements
~~~~~~~~~~~~~~~~~~~

.. automodule:: heatherr.groups.commands
    :members:

Random things
~~~~~~~~~~~~~

.. automodule:: heatherr.random.commands
    :members:
