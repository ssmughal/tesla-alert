"""Test suite for the TeslaConnect class"""

import unittest
from unittest.mock import patch
import re

from tesla_connect import TeslaConnect


class TeslaConnectTestCase(unittest.TestCase):
    """Unit tests for the TeslaConnect class"""

    class MockRequestResponse:
        """Mock class returned from calls to the mock requests module

        This class provides the methods used in TeslaConnect to operate on
        the results of a call to the requests module.  They are expected
        to be overwritten, either through direct replacement or derivation.
        """

        def json(self):
            """Placeholder version of the json() method.

            This method is used to get the response payload of a call to
            the requests module (e.g. requests.get() or requests.post() ).
            """

            pass

    def setUp(self):
        pass

    _mock_config = {
        'username' : 'me@myplace.com',
        'password' : 'pAssw0rd',
        'home_location' : {
            'latitude' : 28.50,
            'longitude' : -101.01
        }
    }

    @patch('requests.post')
    @patch('requests.get')
    def test_get_vehicles_1(self, mock_get, mock_post):
        """Gets a single vehicle when just one is in the user's account.

        When there is just a single mobile-enabled vehicle in the user's
        account, we want to make sure that is what is returned.
        """

        # The mock instance of the requests.post() method needs to only
        # return an object which has a json() method which contains an
        # 'access_token' attribute.  It doesn't matter what the attribute
        # value is, as it's opaque to TeslaConnect.  Thus, we can easily
        # simulate the response object's behavior with a simple lambda
        # expression.  The mock instance of the requests.get() method is a
        # little more complicated, as explained below.

        mock_response_post = self.MockRequestResponse()
        mock_response_post.json = lambda: {'access_token' : 'foo'}
        mock_post.return_value = mock_response_post

        class MockRequestResponseGet(self.MockRequestResponse):
            """Class implementing the response behavior of requests.get().

            The mock instance of the requests.get() method is a little more
            complicated because we call it multiple times in get_vehicles():
            once to get the list of vehicles in the user's Tesla account,
            and then once more for each vehicle, to see if it's enabled for
            mobile access.
            """

            def __init__(self, mock_get):
                self._mock_get = mock_get

            def json(self):
                if self._mock_get.call_count == 1:
                    return {
                        'count' : 1,
                        'response' : [
                            {
                                'id_s' : '888',
                                'display_name' : 'foo',
                                'in_service' : False
                            }
                        ]
                    }
                elif self._mock_get.call_count > 1:
                    return {
                        'response' : True
                    }

        mock_response_get = MockRequestResponseGet(mock_get)
        mock_get.return_value = mock_response_get

        tesla = TeslaConnect(self._mock_config)
        vehicles = tesla.get_vehicles()

        self.assertTrue(len(vehicles) == 1)

    @unittest.mock.patch('requests.post')
    @unittest.mock.patch('requests.get')
    def test_get_vehicles_3(self, mock_get, mock_post):
        """Gets multiple vehicles.

        When there are multiple mobile-enabled vehicles in the user's
        account, we want to make sure that they're all returned.
        """

        # The mock instance of the requests.post() method needs to only
        # return an object which has a json() method which contains an
        # 'access_token' attribute.  It doesn't matter what the attribute
        # value is, as it's opaque to TeslaConnect.  Thus, we can easily
        # simulate the response object's behavior with a simple lambda
        # expression.  The mock instance of the requests.get() method is a
        # little more complicated, as explained below.

        mock_response_post = self.MockRequestResponse()
        mock_response_post.json = lambda: {'access_token' : 'foo'}
        mock_post.return_value = mock_response_post

        class MockRequestResponseGet(self.MockRequestResponse):
            """Class implementing the response behavior of requests.get().

            The mock instance of the requests.get() method is a little more
            complicated because we call it multiple times in get_vehicles():
            once to get the list of vehicles in the user's Tesla account,
            and then once more for each vehicle, to see if it's enabled for
            mobile access.
            """

            def __init__(self, mock_get):
                self._mock_get = mock_get

            def json(self):
                if self._mock_get.call_count == 1:
                    return {
                        'count' : 3,
                        'response' : [
                            {
                                'id_s' : '111',
                                'display_name' : 'foo',
                                'in_service' : False
                            },
                            {
                                'id_s' : '222',
                                'display_name' : 'bar',
                                'in_service' : False
                            },
                            {
                                'id_s' : '333',
                                'display_name' : 'baz',
                                'in_service' : False
                            }
                        ]
                    }
                elif self._mock_get.call_count > 1:
                    return {
                        'response' : True
                    }

        mock_response_get = MockRequestResponseGet(mock_get)
        mock_get.return_value = mock_response_get

        tesla = TeslaConnect(self._mock_config)
        vehicles = tesla.get_vehicles()

        self.assertTrue(len(vehicles) == 3)

    @unittest.mock.patch('requests.post')
    @unittest.mock.patch('requests.get')
    def test_mobile_enabled_vehicles(self, mock_get, mock_post):
        """Account with multiple vehicles, but not all are mobile-enabled.

        When there are multiple mobile-enabled vehicles in the user's
        account, but not all of them are mobile-enabled, we want to make
        sure that only those that are mobile-enabled are returned.
        """

        # The mock instance of the requests.post() method needs to only
        # return an object which has a json() method which contains an
        # 'access_token' attribute.  It doesn't matter what the attribute
        # value is, as it's opaque to TeslaConnect.  Thus, we can easily
        # simulate the response object's behavior with a simple lambda
        # expression.  The mock instance of the requests.get() method is a
        # little more complicated, as explained below.

        mock_response_post = self.MockRequestResponse()
        mock_response_post.json = lambda: {'access_token' : 'foo'}
        mock_post.return_value = mock_response_post

        class MockRequestResponseGet(self.MockRequestResponse):
            """Class implementing the response behavior of requests.get().

            The mock instance of the requests.get() method is a little more
            complicated because we call it multiple times in get_vehicles():
            once to get the list of vehicles in the user's Tesla account,
            and then once more for each vehicle, to see if it's enabled for
            mobile access.
            """

            def __init__(self, mock_get):
                self._mock_get = mock_get

            def json(self):
                if self._mock_get.call_count == 1:
                    return {
                        'count' : 2,
                        'response' : [
                            {
                                'id_s' : '111',
                                'display_name' : 'foo',
                                'in_service' : False
                            },
                            {
                                'id_s' : '222',
                                'display_name' : 'bar',
                                'in_service' : False
                            }
                        ]
                    }
                elif self._mock_get.call_count > 1:
                    # If this call to get() is to check if car '222' is
                    # mobile-enabled, we return true, else return false.

                    (arguments, _) = self._mock_get.call_args
                    if re.search(r'222/mobile_enabled$', arguments[0]):
                        return {
                            'response' : True
                        }
                    else:
                        return {
                            'response' : False
                        }

        mock_response_get = MockRequestResponseGet(mock_get)
        mock_get.return_value = mock_response_get

        tesla = TeslaConnect(self._mock_config)
        vehicles = tesla.get_vehicles()

        self.assertTrue(len(vehicles) == 1)

    @unittest.mock.patch('requests.post')
    @unittest.mock.patch('requests.get')
    def test_in_service_vehicles(self, mock_get, mock_post):
        """Account with multiple vehicles, but some are in service.

        When a vehicle is marked as being in service, we want to
        exclude it from our list of available vehicles that we check
        for being disconnected.
        """

        # The mock instance of the requests.post() method needs to only
        # return an object which has a json() method which contains an
        # 'access_token' attribute.  It doesn't matter what the attribute
        # value is, as it's opaque to TeslaConnect.  Thus, we can easily
        # simulate the response object's behavior with a simple lambda
        # expression.  The mock instance of the requests.get() method is a
        # little more complicated, as explained below.

        mock_response_post = self.MockRequestResponse()
        mock_response_post.json = lambda: {'access_token' : 'foo'}
        mock_post.return_value = mock_response_post

        class MockRequestResponseGet(self.MockRequestResponse):
            """Class implementing the response behavior of requests.get().

            The mock instance of the requests.get() method is a little more
            complicated because we call it multiple times in get_vehicles():
            once to get the list of vehicles in the user's Tesla account,
            and then once more for each vehicle, to see if it's enabled for
            mobile access.
            """

            def __init__(self, mock_get):
                self._mock_get = mock_get

            def json(self):
                if self._mock_get.call_count == 1:
                    return {
                        'count' : 2,
                        'response' : [
                            {
                                'id_s' : '111',
                                'display_name' : 'foo',
                                'in_service' : True
                            },
                            {
                                'id_s' : '222',
                                'display_name' : 'bar',
                                'in_service' : False
                            }
                        ]
                    }
                elif self._mock_get.call_count > 1:
                    return {
                        'response' : True
                    }

        mock_response_get = MockRequestResponseGet(mock_get)
        mock_get.return_value = mock_response_get

        tesla = TeslaConnect(self._mock_config)
        vehicles = tesla.get_vehicles()

        self.assertTrue(len(vehicles) == 1)

    def tearDown(self):
        pass


if __name__ == '__main__':
    unittest.main()
