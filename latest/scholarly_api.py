import requests
from typing import List

authKey = None

class AuthError(Exception):
    '''
    [IMPORTANT] API KEYS ARE NOT YET IMPLEMENTED AND HENCE THIS FUNCTION IS NOT IN USE YET.

    AuthError is a custom exception based on the general exception that is Exception.

    It is used when the Scholarly API key provided is invalid.

    '''
    pass

class InvalidArgument(ValueError):
    '''
    InvalidArgument is a custom exception based on ValueError.

    It is used in cases where specific values for functions are not valid, and more detailed errors are desired.

    '''
    pass

def setKey(key: str) -> None:
    '''
    setKey() is a void function that sets the Scholarly API key for authentication.

    Arguments:

    - key:
        Description: An argument of type string that will contain the API key to be set.
        Valid arguments: Any string

    Raises:

    - None

    '''
    global authKey
    authKey = key

def isValidKey() -> bool:
    '''
    [IMPLICIT FUNCTION] THIS FUNCTION IS MADE TO IMPLICITLY VERIFY KEYS WHEN THE SCHOLARLY API SERVER IS NOT CONTACTED

    isValidKey() is an implicit function that returns a boolean value stating whether a Scholarly API key is valid or not.

    Arguments:

    - [IMPLICIT] authKey:
        Description: Variable of type string derived from global variable authKey that will be checked for validity.

    Raises:

    - ConnectionError: Raised when a successful connection to the API server cannot be made.
    - RequestException: Raised when an unknown general exception is faced from the requests module.
    - JSONDecodeError: Raised when the return of the API server cannot be decoded.
    - Exception: Raised when an unknown error is faced.

    '''
    #Because API keys are not currently implemented, this function will return True for the time being.
    return True

    global authKey
    try:
        r = requests.post('https://api.scholarly.repl.co/verify-key', json={"key": authKey})
        r.raise_for_status()
        return r.json()['valid']
    except Exception as e:
        raise e

def getKey(keyName: str) -> str:
    '''
    getKey() is a function that returns any API keys or authorization bearers necessary.

    Arguments:

    - keyName: 
        Description: An argument of type string that will determine what key will be returned.
        Valid arguments: "openai"

    Raises:

    - AuthError: Raised when an invalid Scholarly API key is set. (NOT IN USE)
    - InvalidArgument: Raised when the keyName argument provided is invalid.
    - ConnectionError: Raised when a successful connection to the API server cannot be made.
    - RequestException: Raised when an unknown general exception is faced from the requests module.
    - JSONDecodeError: Raised when the return of the API server cannot be decoded.
    - Exception: Raised when an unknown error is faced.
    '''
    global authKey

    if keyName != "openai":
        raise InvalidArgument

    try:
        r = requests.post('https://api.scholarly.repl.co/get-key', json={"keyName": keyName}, auth=authKey)
        r.raise_for_status()

        if r.status_code == 403:
            raise AuthError("Invalid Scholarly API key.")

        return r.json()['key']
    except Exception as e:
        raise e

def coachStream(userData: List[str], coachData: List[str], chunkSize = 10):
    '''
    coachStream() is a function that yields a continuous content stream from the language model Coach.

    Arguments:

    - userData: 
        Description: An argument of type list that will provide previous user chat history. Must be in CHRONOLOGICAL order.

    - coachData: 
        Description: An argument of type list that will provide previous coach chat history. Must be in CHRONOLOGICAL order.

    [IMPORTANT] THE LENGTH OF userData MUST ALWAYS BE ONE MORE THAN coachData

    - chunkSize (Optional):
        Description: An argument of type integer that will dictate the maximum size of characters for each chunk of content yielded.
        Defaults to: 10

    Raises:

    - AuthError: Raised when an invalid Scholarly API key is set. (NOT IN USE)
    - InvalidArgument: Raised when the userData and coachData arguments provided are invalid.
    - ConnectionError: Raised when a successful connection to the API server cannot be made.
    - RequestException: Raised when an unknown general exception is faced from the requests module.
    - JSONDecodeError: Raised when the return of the API server cannot be decoded.
    - Exception: Raised when an unknown error is faced.

    '''
    global authKey
    try:
        data = formatMessages(userData,coachData)
    
        with requests.post(
            'https://api.scholarly.repl.co/coach-stream', headers=None, auth=authKey, stream=True, json={"messages": data}
        ) as resp:
            
            resp.raise_for_status()

            if resp.status_code == 403:
                raise AuthError("Invalid Scholarly API key.")

            if resp.status_code == 500:
                raise InvalidArgument("Invalid argument provided.")

            for chunk in resp.iter_content(chunkSize, decode_unicode=True):
                if chunk: yield chunk
    except Exception as e:
        raise e

def formatMessages(userMessages: List[str], coachMessages: List[str]) -> List:
    '''
    [IMPLICIT FUNCTION] THIS FUNCTION IS MADE TO IMPLICITLY FORMAT MESSAGES FOR coachStream()

    formatMessages() is an implicit function that returns a formatted version of previous chats for the syntax of coachStream().

    Arguments:

    - userMessages: 
        Description: An argument of type list that will provide previous chat history of the user's messages. Must be in chronological order.

    - coachMessages:
        Description: An argument of type list that will provide previous chat history of coach's messages. Must be in chronological order.

    Raises:

    - InvalidArgument: Raised when the lists provided don't match proper syntax (the length of userMessages must be one more than coachMessages).

    '''
    messageData = []

    if len(userMessages) != len(coachMessages) + 1:
        raise InvalidArgument("The length of userMessages must be one more than the length of coachMessages.")

    for i in range(len(coachMessages)):
        messageData.append({"role": "user", "content": userMessages[i]})
        messageData.append({"role": "assistant", "content": coachMessages[i]})

    messageData.append({"role": "user", "content": userMessages[-1]})

    return messageData
