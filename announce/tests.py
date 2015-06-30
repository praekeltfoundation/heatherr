from django.test import TestCase, Client, override_settings
from announce.models import Group, Person


def make_post(user_name='bob', user_id='test_id', token='1234abc', text=''):
    return {'token': token,
            'user_name': user_name,
            'user_id': user_id,
            'text': text,
            }


@override_settings(SLACK_TOKEN='1234abc')
class SecurityTestCase(TestCase):
    def test_post_check(self):
        c = Client()
        response = c.get('/announce/', {'token': '1234abc'})
        self.assertFalse(response.content)
        self.assertTrue(response.status_code, 400)

    def test_token_check(self):
        c = Client()
        response = c.post('/announce/',
                          make_post(token='fake')
                          )
        self.assertFalse(response.content)
        self.assertTrue(response.status_code, 400)


@override_settings(SLACK_TOKEN='1234abc')
class AnnounceTestCase(TestCase):
    def setUp(self):
        Group.objects.create(group_name='test_group')
        Person.objects.create(person_name='bob', person_id='test_id')
        p1 = Person(person_name='foo', person_id='1')
        p1.save()
        p2 = Person(person_name='bar', person_id='2')
        p2.save()
        g1 = Group(group_name='apple')
        g1.save()
        g1.person_set.add(p1, p2)
        g2 = Group(group_name='banana')
        g2.save()
        g2.person_set.add(p1)

    def test_group_listing(self):
        c = Client()
        response = c.post('/announce/',
                          make_post(text='list-groups'))
        self.assertTrue('test_group' in response.content)
        # check text after command does not break anything
        response = c.post('/announce/',
                          make_post(text='list-groups other text'))
        self.assertTrue('test_group' in response.content)
        self.assertTrue('apple' in response.content)
        self.assertTrue('banana' in response.content)

    def test_people_in_groups(self):
        c = Client()
        # no group name
        response = c.post('/announce/',
                          make_post(text='people-in-group'))
        self.assertTrue('Please give me a group name in your '
                        + 'bellman command:' in response.content)
        # group name doesn't exist
        response = c.post('/announce/',
                          make_post(text='people-in-group BLAH'))
        self.assertTrue('That group doesn\'t exist' in response.content)
        # no people in group
        response = c.post('/announce/',
                          make_post(text='people-in-group test_group'))
        self.assertTrue('There are currently no people in test_group' in
                        response.content)
        # people in group
        response = c.post('/announce/',
                          make_post(text='people-in-group apple'))
        self.assertTrue('foo' in response.content)
        self.assertTrue('bar' in response.content)
        self.assertFalse('bob' in response.content)
        # people in group
        response = c.post('/announce/',
                          make_post(text='people-in-group banana'))
        self.assertTrue('foo' in response.content)
        self.assertFalse('bar' in response.content)
        self.assertFalse('bob' in response.content)

    def test_list_my_groups(self):
        c = Client()
        # person belongs to no groups
        response = c.post('/announce/',
                          make_post(text='list-my-groups'))
        self.assertTrue('You don\'t seem to belong to any groups' in
                        response.content)
        # standard query
        response = c.post('/announce/',
                          make_post(user_name='foo',
                                    user_id='1',
                                    text='list-my-groups BLAH'))
        self.assertTrue('apple' in response.content)
        self.assertTrue('banana' in response.content)
        self.assertFalse('test_group' in response.content)
        # text after command
        response = c.post('/announce/',
                          make_post(user_name='foo',
                                    user_id='1',
                                    text='list-my-groups BLAH'))
        self.assertTrue('apple' in response.content)
        self.assertTrue('banana' in response.content)
        self.assertFalse('test_group' in response.content)
        self.assertFalse('BLAH' in response.content)

    def test_opt_in(self):
        c = Client()
        # no group name
        response = c.post('/announce/',
                          make_post(text='opt-in'))
        self.assertTrue('Please give me a group name in your '
                        + 'bellman command:' in response.content)
        # group name doesn't exist
        response = c.post('/announce/',
                          make_post(text='opt-in BLAH'))
        self.assertTrue('The group \'BLAH\' doesn\'t exist' in
                        response.content)
        # standard case
        response = c.post('/announce/',
                          make_post(text='opt-in test_group'))
        self.assertTrue('You\'ve been added to test_group' in
                        response.content)
        g = Group.objects.get(group_name='test_group')
        self.assertTrue(Person(person_name='bob', person_id='test_id')
                        in g.person_set.all())
        self.assertTrue(g in Person.objects.get(person_id='test_id')
                                   .groups.all())
        # already belongs to group
        response = c.post('/announce/',
                          make_post(text='opt-in test_group'))
        self.assertTrue('You\'re already part of test_group' in
                        response.content)

    def test_opt_out(self):
        c = Client()
        # no group name
        response = c.post('/announce/',
                          make_post(text='opt-out'))
        self.assertTrue('Please give me a group name in your '
                        + 'bellman command:' in response.content)
        # group name doesn't exist
        response = c.post('/announce/',
                          make_post(text='opt-out BLAH'))
        self.assertTrue('The group \'BLAH\' doesn\'t exist' in
                        response.content)
        # does not belong to group
        response = c.post('/announce/',
                          make_post(text='opt-out test_group'))
        self.assertTrue('You\'re not in test_group'in response.content)
        # standard test case
        g = Group.objects.get(group_name='test_group')
        p = Person.objects.get(person_id='test_id')
        g.person_set.add(p)
        g.save()
        self.assertTrue(p in g.person_set.all())
        self.assertTrue(g in p.groups.all())
        response = c.post('/announce/',
                          make_post(text='opt-out test_group'))
        self.assertTrue('You\'ve been removed from test_group'
                        in response.content)
        self.assertFalse(p in g.person_set.all())
        self.assertFalse(g in p.groups.all())

