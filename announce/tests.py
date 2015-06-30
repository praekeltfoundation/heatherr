from django.test import TestCase, Client, override_settings
from announce.models import Group, Person


def make_post(user_name='bob', user_id='test_id', token='1234abc', text=''):
    return {'token': token,
            'user_name': user_name,
            'user_id': user_id,
            'text': text,
            }


@override_settings(SLACK_TOKEN='1234abc')
class AnnounceTestCase(TestCase):
    def setUp(self):
        Group.objects.create(group_name='test_group')
        Person.objects.create(person_name='bob', person_id='test_id')

    def test_group_listing(self):
        c = Client()
        response = c.post('/announce/', make_post(text='list-groups'))
        self.assertTrue('test_group' in response.content)
        self.assertEqual(1, 1)
        print response.content

    def test_groups(self):
        g = Group.objects.get(group_name='test_group')
        self.assertFalse(g.person_set.all())
