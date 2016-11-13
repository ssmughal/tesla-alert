"""Provide email notification support"""

import smtplib
import logging
import json


class Emailer:
    """Class which handles sending notification emails."""

    def __init__(self, config):
        self._config = config['smtp']
        self._logging_level = config['logging_level']
        self._logger = logging.getLogger(__name__)

    def _get_emails(self):
        """Get a dictionary of email addresses and names.

        Read email addresses (and names) from a text file and import
        them into a dictionary (keyed by email address).  It's possible,
        though, that the dictionary is already inline in our config
        structure, in which case we just copy it.
        """

        emails = {}

        # The way we check for an inline dictionary is if the first
        # character of the supposed filename is '{'.  If it's any other
        # character, we treat it as a filename.

        if self._config['datafile'][0] == '{':
            emails = json.loads(self._config['datafile'])
        else:
            try:
                with open(self._config['datafile'], 'r') as email_file:
                    for line in email_file:
                        (name, email) = line.split(',')
                        emails[email.strip()] = name.strip()
            except FileNotFoundError as err:
                print(err)

        return emails

    def send_emails(self, subject, body):
        """Send emails to a list of recipients.

        Use an SMTP email account to send an email to each address in the
        emails dictionary.  Subject and email body are passed in to this
        function, but the email is personalized with the receiver's name.
        """

        emails = self._get_emails()

        # Connect to the mail server
        server = smtplib.SMTP(self._config['smtp_server'], self._config['smtp_port'])
        if self._config['tls'] is True:
            server.starttls()
        server.login(self._config['account_username'], self._config['account_password'])

        # If the logging level is set to INFO or below (e.g. DEBUG), we
        # turn on debug messages for the SMTP connection.  Above INFO
        # means that the user wants fewer messages, so we don't turn on
        # debug messages.
        if self._logging_level <= logging.INFO:
            server.set_debuglevel(1)
        else:
            server.set_debuglevel(0)

        # Compose and send the mail
        sender = self._config['sender_email_address']
        for (receiver_email, receiver_name) in emails.items():
            message = 'From: ' + self._config['sender_display_name'] + '\n'
            message += 'To: ' + receiver_name + ' <' + receiver_email + '>\n'
            message += 'Subject: ' + subject + '\n\n'
            message += 'Hi ' + receiver_name + ',\n\n'
            message += body

            server.sendmail(sender, receiver_email, message)
        server.quit()

        # TODO:  Received email doesn't have a received time in Outlook (Gmail ok)
