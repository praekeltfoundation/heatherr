.. include:: ../README.rst

Writing a thing that responds to Slash commands.

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
