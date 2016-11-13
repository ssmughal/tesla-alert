"""Module which provides high-level status vehicle status.

This module provides feature-level information about the cars in a user's
account and actions to take on that information.
"""

from tesla_connect import TeslaConnect


def check_plugin_status_all(config):
    """Gets a list of unplugged cars in a user's Tesla account

    Check whether each car in the account is plugged in or not, and return
    a dictionary of those cars (name = vehicle ID, value = vehicle name) that
    are unplugged.  We only want to do this for cars that are in our home
    location, however, so first we filter the list of vehicles to only contain
    those in our home location.
    """

    tesla_connect = TeslaConnect(config['tesla_connect'])
    vehicles = tesla_connect.get_vehicles()

    unplugged_vehicles = {}
    for (vehicle_id, vehicle_name) in vehicles.items():
        if tesla_connect.is_car_at_home(vehicle_id) is True:
            if tesla_connect.is_car_unplugged(vehicle_id) is True:
                unplugged_vehicles[id] = vehicle_name

    return unplugged_vehicles

def compose_disconnect_message(vehicles):
    """Compose a human-readable message to send out as an alert."""

    message = ''
    for (_, vehicle_name) in vehicles.items():
        message += 'Vehicle ' + vehicle_name + ' is disconnected.\n'

    return message
