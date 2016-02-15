from heatherr.tests import CommandTestCase
from freezegun import freeze_time

import responses


class TestTimeZone(CommandTestCase):

    def setUp(self):
        self.slackaccount = self.get_slack_account()

    @responses.activate
    @freeze_time('2016-01-01')
    def test_for(self):
        responses.add(
            responses.POST, 'https://slack.com/api/users.list', json={
                'ok': True,
                'members': [{
                    'id': 'member-id',
                    'name': 'testuser',
                    'real_name': 'Test User',
                    'tz': 'America/Indiana/Indianapolis',
                    'tz_label': 'Eastern Standard Time',
                    'tz_offset': -18000,
                }]
            })
        response = self.send_command('/time for testuser')
        data = response.json()
        self.assertEqual(data, {
            'text': ('<@member-id> is in Eastern Standard Time, '
                     'local time is 7:00 PM')
        })

    @responses.activate
    def test_for_tz_absent(self):
        responses.add(
            responses.POST, 'https://slack.com/api/users.list', json={
                'ok': True,
                'members': [{
                    'id': 'member-id',
                    'name': 'testuser',
                    'tz': None,
                }]
            }
        )
        response = self.send_command('/time for testuser')
        data = response.json()
        self.assertEqual(data, {
            'text': ("I can't tell because <@member-id>'s Slack profile "
                     "has no timezone set.")
        })
