export class InvalidArgumentError extends Error {
  constructor(message) {
    super(message);
    this.name = 'InvalidArgumentError';
  }
}

export class TimeoutError extends Error {
  constructor(message) {
    super(message);
    this.name = 'TimeoutError';
  }
}

function checkError(response) {
  if (response.status === 400) {
    throw new InvalidArgumentError(`Invalid argument. Status: ${response.status}`);
  }
  if (!response.ok) {
    throw new Error(`Failed request. Status: ${response.status}`);
  }
}

export async function getKey(keyName, timeout) {
  try {
    const data = '{"keyName":"' + keyName + '"}';
    const response = await fetch('https://api.scholarly.repl.co/get-key', {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
      body: data,
      signal: AbortSignal.timeout(timeout),
    });

    checkError(response);
    return await response.json();
  } catch (error) {
    if (error.name === 'AbortError') {
      throw new TimeoutError(`getKey Error: ${error.message}`);
    }
    throw error;
  }
}

export async function getSession(timeout) {
  const url = 'https://api.scholarly.repl.co/get-session';
  try {
    const response = await fetch(url, { signal: AbortSignal.timeout(timeout)});
    checkError(response);
    const data = await response.json();
    document.cookie = 'session=' + data;
    return data;
  } catch (error) {
    if (error.name === 'AbortError') {
      throw new TimeoutError(`getSession Error: ${error.message}`);
    }
    else { throw error; }
  }
}


export async function getMessages(session, timeout) {
  const url = 'https://api.scholarly.repl.co/load-messages';
  const data = '{"session":"' + session + '"}';
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
      body: data,
      signal: AbortSignal.timeout(timeout),
    });

    checkError(response);
    return await response.json();
  } catch (error) {
    if (error.name === 'AbortError') {
      throw new TimeoutError(`getMessages Error: ${error.message}`);
    }
    throw error;
  }
}

async function* fetchCoachStream(prompt, session, signal) {
  const response = await fetch("https://api.scholarly.repl.co/coach-stream", {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ prompt: prompt, session: session }),
    signal: signal
  });

  if (!response.ok) {
    throw new Error(`Error: ${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder('utf-8');

  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) {
        break;
      }

      const content = decoder.decode(value, { stream: true });
      yield content;

      if (signal.aborted) {
        break;
      }
    }
  } catch (error) {
    if (error.name === 'AbortError' && reader) {
      await reader.cancel();
    }
    throw error;
  }
}


export async function coachStream(prompt, session, onContentReceived, onStreamFinished, onError, signal) {
  const abortController = new AbortController();
  const onStopped = (manual) => {
    if (onStreamFinished) {
      onStreamFinished(manual);
    }
  };

  try {
    for await (const content of fetchCoachStream(prompt, session, signal ? signal : abortController.signal)) {
      onContentReceived(content);
      if (signal && signal.aborted) {
        abortController.abort();
      }
    }
    onStopped(false);
  }
  catch (err) {
    if (err.name === 'AbortError') {
      onStopped(true);
    } else {
      onError(err);
      onStreamFinished(false);
    }
  }

};
