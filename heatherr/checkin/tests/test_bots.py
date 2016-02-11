import re

from django.test import TestCase

from heatherr.checkin.bots import thankyou
from heatherr.views import BotMessage


class TestBots(TestCase):

    def test_thankyou(self):
        pattern = thankyou.patterns[0]
        self.assertEqual(
            thankyou(
                'bot-user-id', BotMessage({'text': 'hi there!'}),
                re.match(pattern, 'thanks user!')), {
                'text': 'you thanked: user',
                'type': 'message',
                'id': None,
                'channel': None
            })
