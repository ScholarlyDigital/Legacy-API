import requests
from requests.exceptions import RequestException
from requests_toolbelt.multipart import decoder
import contextlib


class InvalidArgumentError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.name = 'InvalidArgumentError'


class TimeoutError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.name = 'TimeoutError'


def check_error(response):
    """
    Checks the response for possible errors and raises appropriate exceptions.

    Args:
        response (requests.Response): The response object to be checked for errors.
    """
    if response.status_code == 400:
        raise InvalidArgumentError(f'Invalid argument. Status: {response.status_code}')
    if not response.ok:
        raise Exception(f'Failed request. Status: {response.status_code}')


def get_key(key_name, timeout):
    """
    Fetches the API key with the provided key name.

    Args:
        key_name (str): The name of the API key to fetch.
        timeout (float): The request timeout in seconds.

    Returns:
        dict: The JSON response containing the API key.
    """
    try:
        data = {"keyName": key_name}
        response = requests.post('https://api.scholarly.repl.co/get-key', json=data, timeout=timeout)
        check_error(response)
        return response.json()
    except RequestException as error:
        if error.__class__.__name__ == 'timeout':
            raise TimeoutError(f'getKey Error: {error}')
        raise error


def get_session(timeout):
    """
    Fetches a new session ID.

    Args:
        timeout (float): The request timeout in seconds.

    Returns:
        dict: The JSON response containing the session ID.
    """
    url = 'https://api.scholarly.repl.co/get-session'
    try:
        response = requests.get(url, timeout=timeout)
        check_error(response)
        data = response.json()
        return data
    except RequestException as error:
        if error.__class__.__name__ == 'timeout':
            raise TimeoutError(f'getSession Error: {error}')
        raise error


def get_messages(session, timeout):
    """
    Fetches the messages for the provided session ID.

    Args:
        session (str): The session ID.
        timeout (float): The request timeout in seconds.

    Returns:
        dict: The JSON response containing the messages for the session.
    """
    url = 'https://api.scholarly.repl.co/load-messages'
    data = {"session": session}
    try:
        response = requests.post(url, json=data, timeout=timeout)
        check_error(response)
        return response.json()
    except RequestException as error:
        if error.__class__.__name__ == 'timeout':
            raise TimeoutError(f'getMessages Error: {error}')
        raise error


@contextlib.contextmanager
def coach_stream(prompt, session, timeout=None):
    """
    Creates a context manager for the coach stream functionality.

    Args:
        prompt (str): The prompt to send to the coach stream.
        session (str): The session ID.
        timeout (float, optional): The request timeout in seconds.

    Yields:
        str: The content chunks returned by the coach stream.
    """
    url = 'https://api.scholarly.repl.co/coach-stream'
    stream_data = {"prompt": prompt, "session": session}
    content_boundary = 'my-boundary'
    headers = {'Content-Type': f'multipart/form-data; boundary={content_boundary}'}

    with requests.post(url, data=stream_data, headers=headers, stream=True, timeout=timeout) as r:
        check_error(r)
        yield from parse_multipart_stream_response(r, content_boundary)


def parse_multipart_stream_response(response, content_boundary):
    """
    Parses the multipart stream response from the coach stream.

    Args:
        response (requests.Response): The response object to be parsed.
        content_boundary (str): The content boundary used in the response.

    Yields:
        str: The content chunks returned by the coach stream.
    """
    multipart_data = decoder.MultipartDecoder.from_response(response)

    for part in multipart_data.parts:
        yield part.content.decode("utf-8")
