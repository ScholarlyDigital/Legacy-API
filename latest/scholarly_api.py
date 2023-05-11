import requests
from requests.exceptions import RequestException
from requests_toolbelt.multipart import decoder
import contextlib
import json


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


def get_key(key_name, timeout=None):
    """
    Fetches the API key with the provided key name.

    Args:
        key_name (str): The name of the API key to fetch.
        timeout (float, optional): The request timeout in seconds.

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


def get_session(timeout=None):
    """
    Fetches a new session ID.

    Args:
        timeout (float, optional): The request timeout in seconds.

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


def get_messages(session, timeout=None):
    """
    Fetches the messages for the provided session ID.

    Args:
        session (str): The session ID.
        timeout (float, optional): The request timeout in seconds.

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
def coach_stream(prompt, session=get_session(), timeout=None):
    """
    Creates a context manager for the coach stream functionality.

    Args:
        prompt (str): The prompt to send to the coach stream.
        session (str): The session ID.
        timeout (float, optional): The request timeout in seconds.

    Yields:
        str: The content chunks returned by the coach stream.
    """
    url = 'https://api.scholarly.repl.co/coach'
    stream_data = json.dumps({"prompt": prompt, "session": session, "stream":True})
    headers = {'Content-Type': 'application/json'}

    with requests.post(url, data=stream_data, headers=headers, stream=True, timeout=timeout) as r:
        check_error(r)
        yield from parse_multipart_stream_response(r)

def coach_response(prompt, session=get_session(), timeout=None):
    """
    Returns a final response for the prompt_coach() fucntion.

    Args:
        prompt (str): The prompt to send to the coach stream.
        session (str): The session ID.
        timeout (float, optional): The request timeout in seconds.

    Returns:
        str: The content returned by the coach.
    """
    url = 'https://api.scholarly.repl.co/coach'
    stream_data = json.dumps({"prompt": prompt, "session": session,"stream":False})
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post(url, data=stream_data, headers=headers, timeout=timeout)
        check_error(response)
        return response.json()
    except RequestException as error:
        if error.__class__.__name__ == 'timeout':
            raise TimeoutError(f'getMessages Error: {error}')
        raise error


def parse_multipart_stream_response(response):
    """
    Parses the multipart stream response from the coach stream.

    Args:
        response (requests.Response): The response object to be parsed.

    Yields:
        str: The content chunks returned by the coach stream.
    """
    lines = response.iter_lines()
    for line in lines:
        decoded_line = line.decode("utf-8")
        if decoded_line:
            yield decoded_line
