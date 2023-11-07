from flask import Flask, jsonify, render_template, send_from_directory, Response, stream_with_context, request
from flask_cors import CORS
import os
import openai
import secrets
import uuid
import json

app = Flask(__name__)
CORS(app, supports_credentials=True)
openai.key = os.environ.get('OPENAI_API_KEY')

tokensInUse = []

class SessionToken:

  def __init__(self, base_dir="sessions"):
    self.base_dir = base_dir
    self.tokens = self.load_tokens()

    if not os.path.exists(self.base_dir):
      os.makedirs(self.base_dir)

  def load_tokens(self):
    if os.path.exists(self.base_dir):
      return os.listdir(self.base_dir)
    else:
      return []

  def get_all(self):
    self.tokens = self.load_tokens()
    return self.tokens

  def load_data(self, token):
    if not self.check_token(token):
      return None

    jsonDir = "sessions/" + token + "/context.json"
    with open(jsonDir, "r") as j:
      return json.load(j)

  def check_token(self, token):
    return token in self.get_all()

  def generate_token(self, prompt):
    global systemMessage
    self.tokens = self.load_tokens()
    while True:
      token = str(uuid.UUID(int=secrets.randbits(128), version=4))
      if token not in self.tokens:
        self.tokens.append(token)
        session_dir = os.path.join(self.base_dir, token)
        os.makedirs(session_dir)
        jsonDir = "sessions/" + token + "/context.json"
        with open(jsonDir, "w") as j:
          json.dump([{"role": "system", "content": prompt}], j)
        txtDir = "sessions/" + token + "/transcript.txt"
        with open(txtDir, 'w') as f:
          f.write('')
        return token


session_tokens = SessionToken()

@app.route('/get-messages', methods=['POST'])
def get_messages():
  sessionToken = request.json["session"]
  if not session_tokens.check_token(sessionToken):
    return 'Invalid token.', 400

  if sessionToken in tokensInUse:
    return 'Token is in use.', 400

  jsonDir = "sessions/" + sessionToken + "/context.json"
  with open(jsonDir, "r") as j:
    return jsonify(json.load(j)[1:])


@app.route('/get-session', methods=['POST'])
def get_session():
  profile = request.json["profile"]
  if not profile or type(profile) != str:
    return 'Invalid request.', 400

  with open('profiles.json', 'r') as f:
    profiles = json.load(f)
  
  try:
    context = profiles[profile]
  except:
    return 'Invalid profile.', 400
  
  return jsonify(session_tokens.generate_token(context))


@app.route('/download-js', methods=['GET'])
def dl_js():
  return send_from_directory('static', 'scholarly_api_latest.js', as_attachment=True)


@app.route('/download-py', methods=['GET'])
def dl_py():
  return send_from_directory('static','scholarly_api_latest.py', as_attachment=True)


@app.route('/cdn-js', methods=['GET'])
def cdn_js():
  return send_from_directory('static', 'scholarly_api_latest.js')


@app.route('/')
def index():
  return render_template('docs.html')


@app.route('/coach', methods=['POST'])
def coach():
  print(tokensInUse)
  sessionToken = request.json["session"]
  if not session_tokens.check_token(sessionToken):
    return 'Invalid token.', 400

  prompt = request.json["prompt"]
  if prompt == None or type(prompt) != str:
    return 'Invalid prompt.', 400

  stream = request.json["stream"]
  if stream == None or type(stream) != bool:
    return 'Invalid stream argument.', 400

  if sessionToken in tokensInUse:
    return 'Session in use.', 403

  tokensInUse.append(sessionToken)

  messageData = session_tokens.load_data(sessionToken)

  if len(messageData) > 11:
    newMessageData = messageData[-10:]
    newMessageData.insert(0, messageData[0])
    messageData = newMessageData

  messageData.append({"role": "user", "content": prompt})

  jsonDir = "sessions/" + sessionToken + "/context.json"
  with open(jsonDir, "w") as j:
    json.dump(messageData, j)

  txtDir = "sessions/" + sessionToken + "/transcript.txt"
  with open(txtDir, 'a') as f:
    f.write("User: " + prompt + "\n\n")

  def generate():
    final = ""
    try:
      txtDir = "sessions/" + sessionToken + "/transcript.txt"
      with open(txtDir, 'a') as f:
        f.write("Coach: ")
      for chunk in openai.ChatCompletion.create(model="gpt-4-1106-preview", messages=messageData, stream=True):
        content = chunk["choices"][0].get("delta", {}).get("content")
        if content is not None:
          final += content
          with open(txtDir, 'a') as f:
            f.write(content)
          yield content
    except GeneratorExit:
      final += "[STOPPED BY USER]"
      with open(txtDir, 'a') as f:
        f.write("[STOPPED BY USER]")
    except:
      final += "[ERROR OCCURED]"
      with open(txtDir, 'a') as f:
        f.write("[ERROR OCCURED]")
      yield "[ERROR OCCURED]"
    finally:
      messageData.append({"role": "assistant", "content": final})

      with open(jsonDir, "w") as j:
        json.dump(messageData, j)

      with open(txtDir, 'a') as f:
        f.write("\n\n")

      tokensInUse.remove(sessionToken)

  if stream:
    response = Response(stream_with_context(generate()), content_type='text/plain')
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response
  else:
    try:
      content = openai.ChatCompletion.create(model="gpt-4-1106-preview",messages=messageData)
      final = content["choices"][0]["message"]["content"]
      messageData.append({"role": "assistant", "content": final})

      with open(jsonDir, "w") as j:
        json.dump(messageData, j)

      txtDir = "sessions/" + sessionToken + "/transcript.txt"
      with open(txtDir, 'a') as f:
        f.write("Coach: " + final + "\n\n")

      tokensInUse.remove(sessionToken)

      return jsonify(final)
    except:
      final = "[ERROR OCCURRED]"
      messageData.append({"role": "assistant", "content": final})

      with open(jsonDir, "w") as j:
        json.dump(messageData, j)

      txtDir = "sessions/" + sessionToken + "/transcript.txt"
      with open(txtDir, 'a') as f:
        f.write("Coach: " + final + "\n\n")

      tokensInUse.remove(sessionToken)

      return jsonify(final)


app.run(host='0.0.0.0', threaded=True)
