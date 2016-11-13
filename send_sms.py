"""Provide SMS notification support."""

import logging
import json

from twilio.rest import TwilioRestClient


class MessageSender:
    """Class which handles sending notification text messages."""

    def __init__(self, config):
        self._config = config['twilio']
        self._logging_level = config['logging_level']
        self._logger = logging.getLogger(__name__)

    def _get_phone_numbers(self):
        """Get a dictionary of phone numbers and names.

        Read phone numbers (and names) from a text file and import them
        into a dictionary (keyed by phone number).  It's possible, though,
        that the dictionary is already inline in our config structure, in
        which case we just copy it.
        """

        phone_numbers = {}

        # The way we check for an inline dictionary is if the first
        # character of the supposed filename is '{'.  If it's any other
        # character, we treat it as a filename.

        if self._config['datafile'][0] == '{':
            phone_numbers = json.loads(self._config['datafile'])
        else:
            try:
                with open(self._config['datafile'], 'r') as numbers_file:
                    for line in numbers_file:
                        (name, number) = line.split(',')
                        phone_numbers[number.strip()] = name.strip()
            except FileNotFoundError as err:
                print(err)

        return phone_numbers

    def send_sms(self, subject, body):
        """Send an SMS to a list of recipients.

        Use the Twilio web service to send an SMS to each phone number in a
        dictionary of numbers that we've obtained from storage.  Subject and
        body are passed in to this function, but each message is customized
        with the receiver's name.
        """

        # Get the phone numbers dictionary.
        phone_numbers = self._get_phone_numbers()

        # Create the Twilio REST client, which we'll use for sending each SMS.
        client = TwilioRestClient(self._config['account_sid'], self._config['auth_token'])

        # Compose and send each SMS.
        for (number, name) in phone_numbers.items():
            self._logger.info("Sending SMS to %s (%s).", name, number)
            message = subject + '. Hi ' + name + ', ' + body
            client.messages.create(to=number, from_=self._config['sending_number'], body=message)
