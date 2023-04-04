import requests

class ScholarlyAPI:
  def __init__(self):
    print("Scholarly API instance initialised.")

  def getKey(self):
    r = requests.get('https://api.scholarly.repl.co/openai')
    try:
      return r.json()['key']
    except requests.exceptions.JSONDecodeError:
      print("Error in decoding JSON. Fetch failed.")
      return None
