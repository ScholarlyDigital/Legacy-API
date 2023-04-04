export async function getKey() {
  try {
    const key = await requestKey();
    return key;
  } catch (error) {
    return undefined;
  }
}

async function requestKey() {
  return new Promise((resolve, reject) => {
    let api = new XMLHttpRequest();
    api.timeout = 12000;

    api.onload = () => {
      console.log("OpenAI key found.");
      resolve(JSON.parse(api.responseText).key);
    };
      
    api.ontimeout = (e) => {
      console.log("Timed out.");
      reject(new Error("Timed out"));
    };

    api.open('GET','https://api.scholarly.repl.co/openai');
    api.send();
  });
}
