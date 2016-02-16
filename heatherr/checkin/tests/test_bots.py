import re
import json

from django.test import TestCase
from django.core.urlresolvers import reverse

from heatherr.checkin.bots import thankyou
from heatherr.views import BotMessage


class TestBots(TestCase):

    def test_thankyou(self):
        pattern = thankyou.patterns[0]
        self.assertEqual(
            thankyou(
                'bot-user-id', 'bot-user-name',
                BotMessage({'text': 'hi there!'}),
                re.match(pattern, 'thanks user!')), {
                'text': 'you thanked: user',
                'type': 'message',
                'id': None,
                'channel': None
            })

    def test_raw_thank_you(self):
        resp = self.client.post(reverse('bots'), data=json.dumps({
            u'text': u'thanks smn',
            u'ts': u'1455664606.000022',
            u'user': u'user-id',
            u'team': u'team-id',
            u'type': u'message',
            u'channel': u'C1000',
        }), content_type='application/json',
            HTTP_X_BOT_USER_ID='bot-user-id',
            HTTP_X_BOT_USER_NAME='bot-user-name')
        [reply] = resp.json()
        self.assertEqual(reply['text'], 'you thanked: smn')
