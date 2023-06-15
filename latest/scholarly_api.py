import requests
from requests.exceptions import RequestException
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
    raise InvalidArgumentError(
      f'Invalid argument. Status: {response.status_code}')
  if not response.ok:
    raise Exception(f'Failed request. Status: {response.status_code}')


def get_key(key_name, timeout=None):
  """
    Fetches the API key with the provided key name.

    Args:
        key_name (str): The name of the API key to fetch.
        timeout (float, optional): The request timeout in seconds.

    Returns:
        str: A string containing the API key.
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
        dict: The string containing the session ID.
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
        list: A list containing the messages for the session. Formatted for OpenAI API.
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


def coach(prompt, session=get_session(), stream=False, timeout=None):
  """
    Prompt the AI language model Coach.

    Args:
        prompt (str): The prompt to send to Coach .
        session (str): The session ID. Defaults to a new session.
        timeout (float, optional): The request timeout in seconds.
        stream (bool, optional); Whether the response should be streamed. Defaults to False.

    Returns (if not streamed):
        str: The final content returned by coach.    
    
    Yields (if streamed):
        str: The content chunks returned by the coach stream.
    """
  url = 'https://api.scholarly.repl.co/coach'
  data = {"session": session, "prompt": prompt, "stream": stream}

  def stream_response():
    with requests.post(url, json=data, timeout=timeout, stream=True) as response:
        for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
          yield chunk
  
  try:
    if stream:
      return stream_response()
    else:
      response = requests.post(url, json=data, timeout=timeout)
      check_error(response)
      return response.json()
  except RequestException as error:
    if error.__class__.__name__ == 'timeout':
      raise TimeoutError(f'Coach Error: {error}')
    raise error
