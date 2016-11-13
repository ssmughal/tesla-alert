# tesla-alert
Python project to alert users about the status of the cars in their Tesla accounts.

Usage:  python main.py --help

Currently, the app only looks for cars parked at the specified home location which
are unplugged, and sends an alert (by SMS using the Twilio service, and optionally
by email as well, using a specified SMTP server).
