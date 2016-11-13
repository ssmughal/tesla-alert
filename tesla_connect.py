"""Module which uses the Tesla REST API to get car information."""

import json
import logging

import requests


class TeslaConnect:
    """Class which encapsulates all usage of the Telsa REST API."""

    # API endpoints
    _portal = 'https://owner-api.teslamotors.com/api/1/vehicles/'
    _owner_api = 'https://owner-api.teslamotors.com'

    # User agent which emulates the Android mobile app
    _version = '2.1.79'
    _model = 'SM-G900V'
    _codename = 'REL'
    _release = '4.4.4'
    _locale = 'en_US'
    _user_agent = ('Model S ' + _version + ' (' + _model + '; Android ' + _codename + ' '
                   + _release + '; ' + _locale + ')')

    def __init__(self, config):
        self._config = config
        self._logger = logging.getLogger(__name__)

        # First, we get the authentication token, which is needed for
        # all subsequent API calls.  Once we get it, we can set it as
        # part of the common HTTP headers.

        self._token = ''
        token_url = TeslaConnect._owner_api + '/oauth/token'
        payload = {
            'grant_type' : 'password',
            'client_id' : 'e4a9949fcfa04068f59abb5a658f2bac0a3428e4652315490b659d5ab3f35a9e',
            'client_secret' : 'c75f14bbadc8bee3a7594412c31416f8300256d7668ea7e6e7f06727bfb9d220'
        }
        payload['email'] = self._config['username']
        payload['password'] = self._config['password']
        response = requests.post(token_url, data=payload)

        authdata = response.json()
        self._token = authdata['access_token']

        self._http_headers = {}
        self._http_headers['Authorization'] = 'Bearer ' + self._token
        self._http_headers['Content-Type'] = 'application/json; charset=utf-8'
        self._http_headers['User-Agent'] = self._user_agent

    def get_vehicles(self):
        """Return a list of all the vehicles in the user's account.

        Construct a dictionary (key = vehicle ID, value = vehicle name)
        of all the cars in a user's account.  We only include in this
        dictionary those cars that are mobile-enabled, however, as only
        those cars can be queried using the car-access APIs.  Also, we
        don't include cars which are marked as being "in service", because
        those cars may also not be accessible, and because we're likely
        not dealing with charging them, anyway.
        """

        vehicles_url = TeslaConnect._portal
        response = requests.get(vehicles_url, headers=self._http_headers)
        vehicles_json = response.json()
        self._logger.info("Vehicle list:\n%s", json.dumps(vehicles_json, indent=4))

        vehicles = {}
        if vehicles_json['count'] > 0:
            for vehicle in vehicles_json['response']:
                if (len(vehicle['id_s']) > 0) and (not vehicle['in_service']):
                    mobile_enabled_url = (TeslaConnect._portal
                                          + vehicle['id_s'] + '/mobile_enabled')
                    response = requests.get(mobile_enabled_url, headers=self._http_headers)
                    mobile_enabled_json = response.json()

                    if mobile_enabled_json['response'] is True:
                        vehicles[vehicle['id_s']] = vehicle['display_name']

        return vehicles

    def is_car_at_home(self, vehicle_id):
        """Check if the passed-in car is at the home location."""

        drive_state_url = (TeslaConnect._portal + vehicle_id + '/data_request/drive_state')
        response = requests.get(drive_state_url, headers=self._http_headers)
        drive_state_json = response.json()
        self._logger.info("Drive state info for vehicle %s:\n%s", vehicle_id,
                          json.dumps(drive_state_json, indent=4))

        # We use a fairly loose comparison of latitude and longitude which puts
        # us within a couple hundred feet of the home location.
        return bool(abs(drive_state_json['response']['latitude']
                        - self._config['home_location']['latitude']) <= 0.0005
                    and abs(drive_state_json['response']['longitude']
                            - self._config['home_location']['longitude']) <= 0.0005)

    def is_car_unplugged(self, vehicle_id):
        """Check if the passed-in car is unplugged or not."""

        charge_status_url = (TeslaConnect._portal + vehicle_id + '/data_request/charge_state')
        response = requests.get(charge_status_url, headers=self._http_headers)
        charge_state_json = response.json()
        self._logger.info("Charge state info for vehicle %s:\n%s", vehicle_id,
                          json.dumps(charge_state_json, indent=4))

        charging_state = charge_state_json['response']['charging_state']
        return bool(charging_state == 'Disconnected')
