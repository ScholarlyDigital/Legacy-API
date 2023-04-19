export async function getKey() {
  try {
    const rawKey = await ajaxGetRequest('https://api.scholarly.repl.co/openai',12000);
    const key = rawKey.key
    console.log("OpenAI key found.");
    return key;
  } catch (error) {
    return undefined;
  }
}

async function ajaxGetRequest(url, waitTime) {
  return new Promise((resolve, reject) => {
    let api = new XMLHttpRequest();
    api.timeout = waitTime;

    api.onload = () => {
      resolve(JSON.parse(api.responseText));
    };
      
    api.ontimeout = (e) => {
      console.log("Timed out.");
      reject(new Error("Timed out"));
    };

    api.open('GET',url);
    api.send();
  });
}

async function* fetchCoachStream(messageData, signal) {
  const serverUrl = "https://api.scholarly.repl.co/coach-stream"

  const response = await fetch(serverUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ messages: messageData }),
    signal: signal
  });

  if (!response.ok) {
    throw new Error(`Error: ${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder('utf-8');

  while (true) {
    const { value, done } = await reader.read();
    if (done) {
      break;
    }

    const content = decoder.decode(value, { stream: true });
    yield content;

    if (signal.aborted) {
      reader.cancel();
      break;
    }
  }
}


export async function coachStream(messageData, onContentReceived, onStreamFinished, onError, signal) {
  const abortController = new AbortController();
  const onStopped = (manual) => {
    if (onStreamFinished) {
      onStreamFinished(manual);
    }
  };

  try {
    for await (const content of fetchCoachStream(messageData, signal ? signal : abortController.signal)) {
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
    }
  }

};


export function createMessagesJSON(userMessages, coachMessages) {
  var messageData = []
  for (let i = 0; i < coachMessages.length; i++) {
    messageData.push({"role":"user","content":userMessages[i]});
    messageData.push({"role":"assistant","content":coachMessages[i]});
  }
  messageData.push({"role":"user","content":userMessages[userMessages.length - 1]});
  return messageData
}
