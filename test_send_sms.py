"""Test suite for the MessageSender class"""

import copy
import logging
import os
import unittest
from unittest.mock import patch, MagicMock

from send_sms import MessageSender


class MessageSenderTestCase(unittest.TestCase):
    """Unit tests for the MessageSender class"""

    _TEST_FILE = 'test_numbers.txt'

    def setUp(self):
        pass

    def tearDown(self):
        try:
            os.remove(self._TEST_FILE)
        except FileNotFoundError:
            pass

    _mock_config = {
        'twilio' : {
            'datafile' : _TEST_FILE,
            'account_sid' : 'FAKE',
            'auth_token' : 'baadf00d',
            'sending_number' : '+14258675309'
        },
        'logging_level' : logging.DEBUG
    }

    @patch('send_sms.TwilioRestClient')
    def test_send_one_message(self, mock_client):
        """Sends a single message using MessageSender.

        When there is just a single user recipient in the list we use
        for sending messages, we verify that a single call to the Twilio
        service is made to send the message.
        """

        # Create a phone numbers file with a single entry.
        with open(self._TEST_FILE, 'w') as numbers_file:
            numbers_file.write('First Recipient, +14255551212')

        # Create a mock object for the result of the call to
        # TwilioRestClient.messages, which is used by MessageSender.
        mock_instance = mock_client.return_value
        mock_instance.messages = MagicMock()

        # Use our message sending class to send a fake message.
        sms_sender = MessageSender(self._mock_config)
        sms_sender.send_sms('Fake subject', 'Fake message')

        self.assertTrue(mock_client.called)
        self.assertTrue(mock_instance.messages.create.call_count == 1)

    @patch('send_sms.TwilioRestClient')
    def test_send_multiple_messages(self, mock_client):
        """Sends multiple messages using MessageSender.

        When there are multiple recipients in the list we use for
        sending messages, we verify that a call to the Twilio service
        is made once per recipient.
        """

        # Create a phone numbers file with a multiple entries.
        with open(self._TEST_FILE, 'w') as numbers_file:
            numbers_file.write('First Recipient, +14255551212\n')
            numbers_file.write('Second Recipient, +14255551213\n')
            numbers_file.write('Third Recipient, +14255551214')

        # Create a mock object for the result of the call to
        # TwilioRestClient.messages, which is used by MessageSender.
        mock_instance = mock_client.return_value
        mock_instance.messages = MagicMock()

        # Use our message sending class to send a fake message.
        sms_sender = MessageSender(self._mock_config)
        sms_sender.send_sms('Fake subject', 'Fake message')

        self.assertTrue(mock_client.called)
        self.assertTrue(mock_instance.messages.create.call_count == 3)

    @patch('send_sms.TwilioRestClient')
    def test_inline_recipients(self, mock_client):
        """Sends to recipients listed directly in config structure.

        If the config structure doesn't contain a file name, but rather
        has the recipients listed inline, we verify that that the SMS
        sending module can handle this.
        """

        # Create a config structure with inline SMS recipients.  We
        # have to be careful not to corrupt the base config structure
        # used by all other tests, though, so we make a deep copy.
        inline_config = copy.deepcopy(self._mock_config)
        inline_config['twilio']['datafile'] = '{"+14255551212": "First Recipient",'
        inline_config['twilio']['datafile'] += '"+14255551213": "Second Recipient"}'

        # Create a mock object for the result of the call to
        # TwilioRestClient.messages, which is used by MessageSender.
        mock_instance = mock_client.return_value
        mock_instance.messages = MagicMock()

        # Use our message sending class to send a fake message.
        sms_sender = MessageSender(inline_config)
        sms_sender.send_sms('Fake subject', 'Fake message')

        self.assertTrue(mock_client.called)
        self.assertTrue(mock_instance.messages.create.call_count == 2)


if __name__ == '__main__':
    unittest.main()
