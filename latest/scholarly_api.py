import requests

def getKey(self):
  r = requests.get('https://api.scholarly.repl.co/openai')
  try:
    return r.json()['key']
  except requests.exceptions.JSONDecodeError:
    print("Error in decoding JSON. Error code:")
    return None

def coachStream(data):
    s = requests.Session()
    with s.post('https://api.scholarly.repl.co/coach-stream', headers=None, stream=True,json={"messages":data}) as resp:
      for char in resp.iter_content(1,decode_unicode=True):
        if char: yield char

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
