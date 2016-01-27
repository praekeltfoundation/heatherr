from django.test import override_settings
from heatherr.tests import CommandTestCase
from heatherr.views import dispatcher


class TestDispatcher(CommandTestCase):

    def test_not_found_handler(self):
        self.assertCommandResponse(
            '/foo bar baz',
            'Sorry, I don\'t know what to do with `/foo`.')

    def test_token(self):
        with override_settings(SLACK_TOKEN='foo'):
            response = self.send_command('/foo', token='baz')
            self.assertContains(
                response, 'Invalid or missing slack token.', status_code=400)

    def test_autodoc(self):
        app = dispatcher.command('/foo')

        @app.respond('baz')
        def baz(request, match):
            """This thing returns baz"""
            return 'baz'

        response = self.send_command('/foo help')
        self.assertContains(response, 'This thing returns baz')
        dispatcher.unregister('/foo')
