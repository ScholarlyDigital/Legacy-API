import requests

def getKey(self):
  r = requests.get('https://api.scholarly.repl.co/openai')
  try:
    return r.json()['key']
  except requests.exceptions.JSONDecodeError as e:
    raise e

def coachStream(data, chunkSize):
    try:
        s = requests.Session()
        with s.post('https://api.scholarly.repl.co/coach-stream', headers=None, stream=True, json={"messages": data}) as resp:
            resp.raise_for_status()
            for chunk in resp.iter_content(chunkSize, decode_unicode=True):
                if chunk: yield chunk
    except RequestException as e:
        raise e
    except Exception as e:
        raise e

def createMessagesJSON(userMessages: list ,coachMessages: list):
  sortedArray = []
  if len(userMessages) != len(coachMessages)+1:
    return None
  for i in range(len(coachMessages)):
    sortedArray.append({"role":"user","content":userMessages[i]})
    sortedArray.append({"role":"assistant","content":coachMessages[i]})
  sortedArray.append({"role":"user","content":userMessages[-1]})
  print(sortedArray)
  return sortedArray
