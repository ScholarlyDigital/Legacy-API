import requests

def getKey(self):
  r = requests.get('https://api.scholarly.repl.co/openai')
  try:
    return r.json()['key']
  except requests.exceptions.JSONDecodeError:
    print("Error in decoding JSON. Error code:")
    return None