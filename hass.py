import urequests as requests
import json

METH_GET = 'GET'
METH_POST = 'POST'

URL_ROOT = '/'
URL_API = '/api/'
URL_API_STREAM = '/api/stream'
URL_API_CONFIG = '/api/config'
URL_API_DISCOVERY_INFO = '/api/discovery_info'
URL_API_STATES = '/api/states'
URL_API_STATES_ENTITY = '/api/states/{}'
URL_API_EVENTS = '/api/events'
URL_API_EVENTS_EVENT = '/api/events/{}'
URL_API_SERVICES = '/api/services'
URL_API_SERVICES_SERVICE = '/api/services/{}/{}'
URL_API_COMPONENTS = '/api/components'
URL_API_ERROR_LOG = '/api/error_log'
URL_API_LOG_OUT = '/api/log_out'
URL_API_TEMPLATE = '/api/template'

HTTP_HEADER_HA_AUTH = 'X-HA-access'
HTTP_HEADER_X_REQUESTED_WITH = 'X-Requested-With'

CONTENT_TYPE = 'Content-Type'
CONTENT_TYPE_JSON = 'application/json'

API_STATUS_OK = "ok"
API_STATUS_INVALID_PASSWORD = "invalid_password"
API_STATUS_CANNOT_CONNECT = "cannot_connect"
API_STATUS_UNKNOWN = "unknown"


class HomeAssistantError(Exception):
    """General Home Assistant exception occurred."""

    pass


class API:
    """Object to pass around Home Assistant API location and credentials."""

    def __init__(self, host: str, api_password: str = None,
                 port: int = 8123,
                 use_ssl: bool = False) -> None:
        """Init the API."""
        self.host = host
        self.port = port
        self.api_password = api_password

        if host.startswith("http://") or host.startswith("https://"):
            self.base_url = host
        elif use_ssl:
            self.base_url = "https://{}".format(host)
        else:
            self.base_url = "http://{}".format(host)

        if port is not None:
            self.base_url += ':{}'.format(port)

        self.status = None
        self._headers = {CONTENT_TYPE: CONTENT_TYPE_JSON}

        if api_password is not None:
            self._headers[HTTP_HEADER_HA_AUTH] = api_password

    def validate_api(self, force_validate: bool = False) -> bool:
        """Test if we can communicate with the API."""
        if self.status is None or force_validate:
            self.status = validate_api(self)

        return self.status == API_STATUS_OK

    def __call__(self, method: str, path: str, data=None,
                 timeout: int = 5) -> requests.Response:
        """Make a call to the Home Assistant API."""
        if data is None:
            data_str = None
        else:
            data_str = json.dumps(data)

        url = self.base_url + path

        try:
            if method == METH_GET:
                return requests.get(
                    url, params=data_str, timeout=timeout,
                    headers=self._headers)

            return requests.request(
                method, url, data=data_str, timeout=timeout,
                headers=self._headers)

        except requests.exceptions.ConnectionError:
            print("Error connecting to server")
            raise HomeAssistantError("Error connecting to server")

        except requests.exceptions.Timeout:
            error = "Timeout when talking to {}".format(self.host)
            print(error)
            raise HomeAssistantError(error)

    def __repr__(self) -> str:
        """Return the representation of the API."""
        return "<API({}, password: {})>".format(
            self.base_url, 'yes' if self.api_password is not None else 'no')


def validate_api(api: API):
    """Make a call to validate API."""
    try:
        req = api(METH_GET, URL_API)

        if req.status_code == 200:
            return API_STATUS_OK

        if req.status_code == 401:
            return API_STATUS_INVALID_PASSWORD

        return API_STATUS_UNKNOWN

    except HomeAssistantError:
        return API_STATUS_CANNOT_CONNECT


class Thermostat:
    __slots__ = ['id']

    def __init__(self, entity_id):
        self.id = entity_id
