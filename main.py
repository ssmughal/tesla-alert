"""Notify users that one or more of their Teslas are unplugged.

This is the main module of an app which gets the current charge status
for all the cars in a user's Tesla account, and if any of those cars
are both unplugged and at the home location, notifies a series of users
(as specified in a file).
"""

import getopt
import json
import logging
import os
import sys

import charge_status
from send_sms import MessageSender
from emailer import Emailer


def map_logging_level_string(level_string):
    """Convert string to its equivalent logging level."""

    if str.lower(level_string) == 'debug':
        logging_level = logging.DEBUG
    elif str.lower(level_string) == 'info':
        logging_level = logging.INFO
    elif str.lower(level_string) == 'warning':
        logging_level = logging.WARNING
    elif str.lower(level_string) == 'error':
        logging_level = logging.ERROR
    elif str.lower(level_string) == 'critical':
        logging_level = logging.CRITICAL
    else:
        # Our default logging level is warning and above.
        logging_level = logging.WARNING

    return logging_level

def load_configuration_file():
    """Load our configuration from permanent storage.

    Our configuration is stored in a JSON file which we load into an
    in-memory dictionary.  Some values in the dictionary may later be
    overwritten by environment variables and/or command-line arguments,
    but some configuration values can only be set in the JSON file, so
    we require it to exist and will terminate with an exception if it
    does not.
    """

    config_file = open('config.json', 'r')
    config = json.load(config_file)
    config_file.close()

    # The logging level set in the JSON file is a simple string, and
    # needs to be converted to a number (an enum, in effect) which can
    # be understood by the logging module.
    config['logging_level'] = map_logging_level_string(config['logging_level'])

    return config

def process_environment_vars(config):
    """Process environment variables, return results.

    We're given an existing set of configuration settings, and any
    environment variables that we process replace those in the existing
    set.
    """

    # Environment variables for the Tesla REST API.
    tesla_config = config['tesla_connect']
    if 'TESLAALERT_USERNAME' in os.environ:
        tesla_config['username'] = os.environ['TESLAALERT_USERNAME']
    if 'TESLAALERT_PASSWORD' in os.environ:
        tesla_config['password'] = os.environ['TESLAALERT_PASSWORD']
    if 'TESLAALERT_HOME_LATITUDE' in os.environ:
        tesla_config['home_location']['latitude'] = float(os.environ['TESLAALERT_HOME_LATITUDE'])
    if 'TESLAALERT_HOME_LONGITUDE' in os.environ:
        tesla_config['home_location']['longitude'] = float(os.environ['TESLAALERT_HOME_LONGITUDE'])

    # Environment variables for the Twilio REST API.
    twilio_config = config['twilio']
    if 'TESLAALERT_TWILIO_DATAFILE' in os.environ:
        twilio_config['datafile'] = os.environ['TESLAALERT_TWILIO_DATAFILE']
    if 'TESLAALERT_TWILIO_ACCOUNT_SID' in os.environ:
        twilio_config['account_sid'] = os.environ['TESLAALERT_TWILIO_ACCOUNT_SID']
    if 'TESLAALERT_TWILIO_AUTH_TOKEN' in os.environ:
        twilio_config['auth_token'] = os.environ['TESLAALERT_TWILIO_AUTH_TOKEN']
    if 'TESLAALERT_TWILIO_SENDING_NUMBER' in os.environ:
        twilio_config['sending_number'] = os.environ['TESLAALERT_TWILIO_SENDING_NUMBER']

    # Environment variables for the SMTP server we're using.
    smtp_config = config['smtp']
    if 'TESLAALERT_SMTP_DATAFILE' in os.environ:
        smtp_config['datafile'] = os.environ['TESLAALERT_SMTP_DATAFILE']
    if 'TESLAALERT_SMTP_SERVER' in os.environ:
        smtp_config['smtp_server'] = os.environ['TESLAALERT_SMTP_SERVER']
    if 'TESLAALERT_SMTP_PORT' in os.environ:
        smtp_config['smtp_port'] = int(os.environ['TESLAALERT_SMTP_PORT'])
    if 'TESLAALERT_SMTP_USERNAME' in os.environ:
        smtp_config['account_username'] = os.environ['TESLAALERT_SMTP_USERNAME']
    if 'TESLAALERT_SMTP_PASSWORD' in os.environ:
        smtp_config['account_password'] = os.environ['TESLAALERT_SMTP_PASSWORD']
    if 'TESLAALERT_SMTP_USE_TLS' in os.environ:
        smtp_config['tls'] = bool(int(os.environ['TESLAALERT_SMTP_USE_TLS']))
    if 'TESLAALERT_SMTP_SENDER_EMAIL' in os.environ:
        smtp_config['sender_email_address'] = os.environ['TESLAALERT_SMTP_SENDER_EMAIL']
    if 'TESLAALERT_SMTP_SENDER_DISPLAY' in os.environ:
        smtp_config['sender_display_name'] = os.environ['TESLAALERT_SMTP_SENDER_DISPLAY']

    # "Free-floating" environment variables.
    if 'TESLAALERT_SEND_EMAIL' in os.environ:
        config['send_email'] = bool(int(os.environ['TESLAALERT_SEND_EMAIL']))
    if 'TESLAALERT_LOGGING_LEVEL' in os.environ:
        config['logging_level'] = os.environ['TESLAALERT_LOGGING_LEVEL']

    return config

def usage(script_name):
    """Print out the usage information."""

    usage_string = "\nUsage:\n  python " + script_name + " [options]\n\n"
    usage_string += "Options:\n"
    usage_string += "  -h, --help                    Show help.\n"
    usage_string += "  -u, --username <string>       User's Tesla account username.\n"
    usage_string += "  -p, --password <string>       User's Tesla account password.\n"
    usage_string += "  --latitude <decimal>          Latitude of home location.\n"
    usage_string += "  --longitude <decimal>         Longitude of home location.\n"
    usage_string += "  -e, --email                   "
    usage_string += "Alert users with email (in addition to a text message).\n"
    usage_string += "  -l, --loglevel <string>       "
    usage_string += "Set the logging level (debug, warning, etc.).\n"
    usage_string += "\n"

    print(usage_string)

def process_command_line(config, argv):
    """Process command-line arguments, return results.

    We're given an existing set of configuration settings, and any
    command-line arguments that we process replace those in the
    existing set.
    """

    try:
        (opts, _) = getopt.getopt(argv[1:], 'heu:p:l:', [
            'help', 'email', 'username=', 'password=', 'loglevel=', 'latitude=', 'longitude='])
    except getopt.GetoptError:
        usage(argv[0])
        sys.exit(2)

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage(argv[0])
            sys.exit()
        elif opt in ('-u', '--username'):
            config['tesla_connect']['username'] = arg
        elif opt in ('-p', '--password'):
            config['tesla_connect']['password'] = arg
        elif opt in ('--latitude',):
            config['tesla_connect']['home_location']['latitude'] = float(arg)
        elif opt in ('--longitude',):
            config['tesla_connect']['home_location']['longitude'] = float(arg)
        elif opt in ('-e', '--email'):
            config['send_email'] = True
        elif opt in ('-l', '--loglevel'):
            config['logging_level'] = map_logging_level_string(arg)

    return config

def main(argv):
    """Top-level function."""

    # The order of precedence for settings which this program needs in
    # order to function is (from highest precedence to lowest) is:
    # command-line argument, environment variable, configuration file
    # value.  So the way we handle this is to read the configuration
    # file into our in-memory configuration data structure first, then
    # read environment variables (which can overwrite values already in
    # the in-memory structure), and finally process the command line.

    config = load_configuration_file()
    config = process_environment_vars(config)
    config = process_command_line(config, argv)

    logging.basicConfig(level=config['logging_level'])
    logging.getLogger(__name__).debug("Final config after all processing:\n%s",
                                      json.dumps(config, indent=4))

    # Do the main work of the program:  for every unplugged vehicle in
    # the home location, compose a message for the user.  Send the message
    # using text messages and optionally emails as well.

    unplugged_vehicles = charge_status.check_plugin_status_all(config)
    if len(unplugged_vehicles) > 0:
        message = charge_status.compose_disconnect_message(unplugged_vehicles)
        print(message)
        sms_sender = MessageSender(config)
        sms_sender.send_sms('Alert:  Tesla charge status', message)
        if config['send_email'] is True:
            emailer = Emailer(config)
            emailer.send_emails('Alert:  Tesla charge status', message)


if __name__ == '__main__':
    main(sys.argv)
