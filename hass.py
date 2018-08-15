import ujson as json

import urequests as requests

METH_GET = 'GET'
METH_POST = 'POST'

# URL_ROOT = '/'
# URL_API = '/api/'
# URL_API_STREAM = '/api/stream'
# URL_API_CONFIG = '/api/config'
# URL_API_DISCOVERY_INFO = '/api/discovery_info'
# URL_API_STATES = '/api/states'
URL_API_STATES_ENTITY = '/api/states/{}'
# URL_API_EVENTS = '/api/events'
# URL_API_EVENTS_EVENT = '/api/events/{}'
# URL_API_SERVICES = '/api/services'
URL_API_SERVICES_SERVICE = '/api/services/{}/{}'
# URL_API_COMPONENTS = '/api/components'
# URL_API_ERROR_LOG = '/api/error_log'
# URL_API_LOG_OUT = '/api/log_out'
# URL_API_TEMPLATE = '/api/template'

HTTP_HEADER_HA_AUTH = 'X-HA-access'
# HTTP_HEADER_X_REQUESTED_WITH = 'X-Requested-With'

CONTENT_TYPE = 'Content-Type'
CONTENT_TYPE_JSON = 'application/json'


class API:
    """Object to pass around Home Assistant API location and credentials."""
    __slots__ = ['base_url', 'api_password', '_headers']

    def __init__(self, base_url: str, api_password: str = None) -> None:
        """Init the API."""
        self.base_url = base_url
        self.api_password = api_password
        self._headers = {CONTENT_TYPE: CONTENT_TYPE_JSON}

        if api_password is not None:
            self._headers[HTTP_HEADER_HA_AUTH] = api_password

    def __call__(self, method: str, path: str, data=None,
                 timeout: int = 5) -> requests.Response:
        """Make a call to the Home Assistant API."""
        if data is None:
            data_str = None
        else:
            data_str = json.dumps(data)
        url = self.base_url + path
        if method == METH_GET:
            return requests.get(url, headers=self._headers)
        return requests.request(method, url, data=data_str, headers=self._headers)

    def __repr__(self) -> str:
        """Return the representation of the API."""
        return "<API({}, password: {})>".format(
            self.base_url, 'yes' if self.api_password is not None else 'no')


class Thermostat:
    __slots__ = ['id']

    def __init__(self, entity_id):
        self.id = entity_id
