export async function getKey() {
  try {
    const key = await ajaxGetRequest('https://api.scholarly.repl.co',12000);
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
      resolve(JSON.parse(api.responseText).key);
    };
      
    api.ontimeout = (e) => {
      console.log("Timed out.");
      reject(new Error("Timed out"));
    };

    api.open('GET',url);
    api.send();
  });
}
