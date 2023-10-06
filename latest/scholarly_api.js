/**
 * Represents an error for invalid arguments passed to a function.
 */
export class InvalidArgumentError extends Error {
    constructor(message) {
      super(message);
      this.name = 'InvalidArgumentError';
    }
  }
  
  /**
   * Represents a custom error class for timeouts.
   */
  export class TimeoutError extends Error {
    constructor(message) {
      super(message);
      this.name = 'TimeoutError';
    }
  }
  
  /**
   * Checks the response for possible errors and throws appropriate exceptions.
   * @param {Response} response - The response object to be checked for errors.
   */
  function checkError(response) {
    if (response.status === 400) {
      throw new InvalidArgumentError(`Invalid argument. Status: ${response.status}`);
    }
    if (!response.ok) {
      throw new Error(`Failed request. Status: ${response.status}`);
    }
  }
  
  /**
   * Fetches a new session ID.
   * @param {string} profile - The profile for Coach.
   * @param {number} timeout - The request timeout in milliseconds.
   * @returns {Promise} A promise that resolves to the JSON response containing the session ID.
   */
  export async function getSession(profile, timeout) {
    const url = 'https://api.scholarly.repl.co/get-session';
    if (profile === undefined) profile = "default";
    const data = '{"profile":"' + profile + '"}';
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
        throw new TimeoutError(`getSession Error: ${error.message}`);
      }
      throw error;
    }
  }
  
  /**
   * Fetches the messages for the provided session ID.
   * @param {string} session - The session ID.
   * @param {number} timeout - The request timeout in milliseconds.
   * @returns {Promise} A promise that resolves to the JSON response containing the messages for the session.
   */
  export async function getMessages(session, timeout) {
    const url = 'https://api.scholarly.repl.co/get-messages';
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
  
  /**
   * Fetches the coach stream for the given prompt and session ID, returning an async generator with content chunks.
   * @param {string} prompt - The prompt to send to the coach stream.
   * @param {string} session - The session ID.
   * @param {AbortSignal} signal - The optional AbortSignal for handling cancellations.
   * @returns {AsyncGenerator} An async generator that yields content chunks from the coach stream.
   */
  async function* fetchCoachStream(prompt, session, signal) {
    const response = await fetch("https://api.scholarly.repl.co/coach", {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ prompt: prompt, session: session, stream: true }),
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
  
  /**
   * Fetches a response from Coach.
   * @param {string} prompt - The prompt to send to coach.
   * @param {string} session - The session ID.
   * @param {number} timeout - The request timeout in milliseconds.
   * @returns {Promise} A promise that resolves to the coach response.
   */
  export async function coachResponse(prompt, session, timeout) {
    const url = 'https://api.scholarly.repl.co/coach';
    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ prompt: prompt, session: session, stream: false }),
        signal: AbortSignal.timeout(timeout),
      });
  
      checkError(response);
      return await response.json();
    } catch (error) {
      if (error.name === 'AbortError') {
        throw new TimeoutError(`coachResponse Error: ${error.message}`);
      }
      throw error;
    }
  }
  
  /**
   * Streams content from the coach API given a prompt and sessionID.
   * @param {string} prompt - The prompt to send to coach.
   * @param {string} session - The session ID. Defaults to a new session.
   * @param {function} onContentReceived - Callback function for handling content received.
   * @param {function} onStreamFinished - Callback function for when the stream has finished.
   * @param {function} onError - Callback function for handling errors during streaming.
   * @param {AbortSignal} signal - The optional AbortSignal for handling cancellations.
   */
  export async function coachStream(prompt, session=getSession(null), onContentReceived, onStreamFinished, onError, signal) {
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
