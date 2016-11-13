"""Test suite for the Emailer class"""

import copy
import logging
import os
import unittest
from unittest.mock import patch, MagicMock

from emailer import Emailer


class EmailerTestCase(unittest.TestCase):
    """Unit tests for the Emailer class"""

    _TEST_FILE = 'test_emails.txt'

    def setUp(self):
        pass

    def tearDown(self):
        try:
            os.remove(self._TEST_FILE)
        except FileNotFoundError:
            pass

    _mock_config = {
        'smtp': {
            'datafile': 'test_emails.txt',
            'smtp_server': 'smtp.fakeserver.com',
            'smtp_port': 587,
            'tls': True,
            'account_username': 'foo@fakeserver.com',
            'account_password': 'badpassword',
            'sender_email_address': 'foo@fakeserver.com',
            'sender_display_name': 'Foo Bar <foo@fakeserver.com>'
        },
        'logging_level' : logging.DEBUG
    }

    @patch('emailer.smtplib.SMTP')
    def test_send_one_email(self, mock_smtp):
        """Sends a single email using Emailer.

        When there is just a single user recipient in the list we use
        for sending emails, we verify that a single call to the smtp
        service is made to send the email.
        """

        # Create an emails file with a single entry.
        with open(self._TEST_FILE, 'w') as emails_file:
            emails_file.write('First Recipient, first.recipient@whatever.com')

        # Create a mock object for the SMTP server that the Emailer
        # module uses (the return value from a call to smtplib.SMTP).
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server

        # Use our email sending class to send a fake email.
        emailer = Emailer(self._mock_config)
        emailer.send_emails('Fake subject', 'Fake message')

        self.assertTrue(mock_smtp.called)
        self.assertTrue(mock_server.login.called)
        self.assertTrue(mock_server.starttls.called)
        self.assertTrue(mock_server.sendmail.call_count == 1)

    @patch('emailer.smtplib.SMTP')
    def test_send_multiple_emails(self, mock_smtp):
        """Sends multiple emails using Emailer.

        When there are multiple recipients in the list we use for
        sending messages, we verify that a call to the Twilio service
        is made once per recipient.
        """

        # Create a emails file with a multiple entries.
        with open(self._TEST_FILE, 'w') as numbers_file:
            numbers_file.write('First Recipient, first.recipient@whatever.com\n')
            numbers_file.write('Second Recipient, second.recipient@whatever.com\n')
            numbers_file.write('Third Recipient, third.recipient@whatever.com')

        # Create a mock object for the SMTP server that the Emailer
        # module uses (the return value from a call to smtplib.SMTP).
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server

        # Use our email sending class to send a fake email.
        emailer = Emailer(self._mock_config)
        emailer.send_emails('Fake subject', 'Fake message')

        self.assertTrue(mock_smtp.called)
        self.assertTrue(mock_server.login.called)
        self.assertTrue(mock_server.sendmail.call_count == 3)

    @patch('emailer.smtplib.SMTP')
    def test_send_one_email_no_tls(self, mock_smtp):
        """Sends an email to a server without TLS.

        When the config structure says to not use TLS for sending to
        the email server, we make sure to not call the 'starttls' method.
        """

        # Create an emails file with a single entry.
        with open(self._TEST_FILE, 'w') as emails_file:
            emails_file.write('First Recipient, first.recipient@whatever.com')

        # Create a mock object for the SMTP server that the Emailer
        # module uses (the return value from a call to smtplib.SMTP).
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server

        # Mark the SMTP server we use as not accepting TLS.
        self._mock_config['smtp']['tls'] = False

        # Use our email sending class to send a fake email.
        emailer = Emailer(self._mock_config)
        emailer.send_emails('Fake subject', 'Fake message')

        self.assertTrue(mock_smtp.called)
        self.assertTrue(mock_server.login.called)
        self.assertFalse(mock_server.starttls.called)
        self.assertTrue(mock_server.sendmail.call_count == 1)

    @patch('emailer.smtplib.SMTP')
    def test_inline_recipients(self, mock_smtp):
        """Send to recipients listed directly in config structure.

        If the config structure doesn't contain a file name, but rather
        has the recipients listed inline, we verify that the Emailer
        module can handle this.
        """

        # Create a config structure with inline email recipients.  We
        # have to be careful not to corrupt the base config structure
        # used by all other tests, though, so we make a deep copy.
        inline_config = copy.deepcopy(self._mock_config)
        inline_config['smtp']['datafile'] = '{"first.recipient@there.com": "First Recipient",'
        inline_config['smtp']['datafile'] += '"second.recipient@there.com": "Second Recipient"}'

        # Create a mock object for the SMTP server that the Emailer
        # module uses (the return value from a call to smtplib.SMTP).
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server

        # Use our email sending class to send a fake email.
        emailer = Emailer(inline_config)
        emailer.send_emails('Fake subject', 'Fake message')

        self.assertTrue(mock_smtp.called)
        self.assertTrue(mock_server.login.called)
        self.assertTrue(mock_server.sendmail.call_count == 2)


if __name__ == '__main__':
    unittest.main()
