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

DOMAIN_CLIMATE = 'climate'
SERVICE_SET_TEMPERATURE = "set_temperature"
SERVICE_SET_OP_MODE = "set_operation_mode"


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

    def __call__(self, method: str, path: str, data=None) -> requests.Response:
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


def get_state(api: API, entity_id: str):
    """Query given API for state of entity_id."""
    try:
        req = api(METH_GET, URL_API_STATES_ENTITY.format(entity_id))

        # req.status_code == 422 if entity does not exist

        return req.json() \
            if req.status_code == 200 else None

    except (ValueError, OSError):
        return None


def call_service(api: API, domain: str, service: str, service_data=None) -> bool:
    """Call a service at the remote API."""
    try:
        req = api(METH_POST,
                  URL_API_SERVICES_SERVICE.format(domain, service),
                  service_data)

        if req.status_code != 200:
            print("Error calling service: %d - %s", req.status_code, req.text)
            return False
        return True

    except (ValueError, OSError):
        print("Error calling service")
        return False


class Thermostat:
    __slots__ = ['id', 'api']

    def __init__(self, api: API, entity_id):
        self.api = api
        self.id = entity_id

    def get_state(self):
        return get_state(self.api, self.id)

    def set_temperature(self, value: float):
        call_service(self.api, DOMAIN_CLIMATE, SERVICE_SET_TEMPERATURE, {
            "entity_id": self.id,
            "temperature": value
        })

    def turn_off(self):
        call_service(self.api, DOMAIN_CLIMATE, SERVICE_SET_OP_MODE, {
            "entity_id": self.id,
            "operation_mode": "off"
        })

    def set_heat_mode(self):
        call_service(self.api, DOMAIN_CLIMATE, SERVICE_SET_OP_MODE, {
            "entity_id": self.id,
            "operation_mode": "heat"
        })
