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

async function* fetchCoachStream(messageData) {
  const serverUrl = "https://api.scholarly.repl.co/coach-stream"

  const response = await fetch(serverUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ messages: messageData }),
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
  }
}

export async function coachStream(messageData, onContentReceived, onStreamFinished, onError) {
  try {
    for await (const content of fetchCoachStream(messageData)) {
      onContentReceived(content);
    }
  } 
  catch (err) {
    onError(err);
  }
  finally {
    if (onStreamFinished) {
      onStreamFinished();
    }
  }
}
