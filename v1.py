from flask import Blueprint, jsonify, send_from_directory, Response, stream_with_context, request, url_for
import os
import openai
import secrets
import uuid
import json

client = openai.OpenAI()
branch_name = 'v1'
branch = Blueprint(branch_name, __name__)

tokensInUse = []
max_tokens = 4096

class SessionToken:

  def __init__(self, base_dir=f"uploads/{branch_name}/sessions"):
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

    jsonDir = f"uploads/{branch_name}/sessions/" + token + "/context.json"
    with open(jsonDir, "r") as j:
      return json.load(j)

  def check_token(self, token):
    return token in self.get_all()

  def generate_token(self, prompt, image, model):
    global systemMessage
    self.tokens = self.load_tokens()
    while True:
      token = str(uuid.UUID(int=secrets.randbits(128), version=4))
      if token not in self.tokens:
        self.tokens.append(token)
        session_dir = os.path.join(self.base_dir, token)
        os.makedirs(session_dir)
        jsonDir = f"uploads/{branch_name}/sessions/" + token + "/context.json"
        with open(jsonDir, "w") as j:
          json.dump([{"image":image,"count":0,"model":model},[{"role": "system", "content": prompt}]], j)
        txtDir = f"uploads/{branch_name}/sessions/" + token + "/transcript.txt"
        with open(txtDir, 'w') as f:
          f.write('')
        return token


session_tokens = SessionToken()

@branch.route('/get-messages', methods=['POST'])
def get_messages():
  sessionToken = request.json["session"]
  if not session_tokens.check_token(sessionToken):
    return 'Invalid token.', 400

  if sessionToken in tokensInUse:
    return 'Token is in use.', 400

  jsonDir = f"uploads/{branch_name}/sessions/" + sessionToken + "/context.json"
  with open(jsonDir, "r") as j:
    return jsonify(json.load(j)[1][1:])


@branch.route('/get-session', methods=['POST'])
def get_session():
  profile = request.json["profile"]
  if not profile or type(profile) != str:
    return 'Invalid request.', 400

  jsonDir = f'uploads/{branch_name}/profiles.json'
  
  with open(jsonDir, 'r') as f:
    profiles = json.load(f)

  image = False

  if profile == "vision":
    image = True
    model = "gpt-4-vision-preview"
  else:
    image = False
    model = "gpt-4-1106-preview"

  try:
    context = profiles[profile]
  except:
    return 'Invalid profile.', 400

  return jsonify(session_tokens.generate_token(context, image, model))

@branch.route('/image/<session>/<id>')
def view_image(session,id):
  try:
    return send_from_directory('uploads',f'{branch_name}/sessions/{session}/{id}.png')
  except:
    try:
      return send_from_directory('uploads',f'{branch_name}/sessions/{session}/{id}.jpg')
    except:
      return send_from_directory('uploads',f'{branch_name}/sessions/{session}/{id}.jpeg')


@branch.route('/coach', methods=['POST'])
def coach():
  json_data = json.loads(request.files['json'].read().decode('utf-8'))
  sessionToken = json_data["session"]
  if not session_tokens.check_token(sessionToken):
    return 'Invalid token.', 400

  prompt = json_data["prompt"]
  if prompt == None or type(prompt) != str:
    return 'Invalid prompt.', 400

  stream = json_data["stream"]
  if stream == None or type(stream) != bool:
    return 'Invalid stream argument.', 400

  if sessionToken in tokensInUse:
    return 'Session in use.', 403

  image_enabled = False

  if 'image' in request.files:
    if not session_tokens.load_data(sessionToken)[0]['image']:
      return 'Images not allowed for this session.', 403
    else:
      if request.files['image'].content_type != 'image/jpeg' and request.files['image'].content_type != 'image/png' and request.files['image'].content_type != 'image/jpg':
        return 'Invalid image format.', 400
      image_type = request.files['image'].content_type[6:]
      image_enabled = True

  sessionData = session_tokens.load_data(sessionToken)

  def limit_message():
    message = 'The conversation length has reached it\'s limit. Please start a new chat session.'
    for letter in message:
      yield letter
  
  if image_enabled:
    if len(sessionData[1]) > 21:
      if stream:
        response = Response(stream_with_context(limit_message()), content_type='text/plain')
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
      else:
        return jsonify('The conversation length has reached it\'s limit. Please start a new chat session.')  
  else:
    if len(sessionData[1]) > 11:
      if stream:
        response = Response(stream_with_context(limit_message()), content_type='text/plain')
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
      else:
        return jsonify('The conversation length has reached it\'s limit. Please start a new chat session.')  

  tokensInUse.append(sessionToken)
  
  if image_enabled:
    image_count = sessionData[0]['count']
    image_count += 1
    sessionData[0]['count'] = image_count
    request.files['image'].save(f'uploads/{branch_name}/sessions/{sessionToken}/{image_count}.{image_type}')
    base_url = url_for('index', _external=True).replace('http','https')
    image_url = f'{base_url}{branch_name}/image/{sessionToken}/{image_count}'
  messageData = sessionData[1]
  model = sessionData[0]['model'] 

  if not image_enabled:
    messageData.append({"role": "user", "content":[{"type":"text","text":prompt}]})
  else:
    messageData.append({"role": "user","content":[{"type":"image_url","image_url":{"url":image_url,"detail":"high"}},{"type":"text","text":prompt}]})

  jsonDir = f"uploads/{branch_name}/sessions/" + sessionToken + "/context.json"
  with open(jsonDir, "w") as j:
    json.dump([sessionData[0],messageData], j)

  txtDir = f"uploads/{branch_name}/sessions/" + sessionToken + "/transcript.txt"
  with open(txtDir, 'a') as f:
    if image_enabled:
      f.write("User: (Image #"+ str(image_count) + " attached) " + prompt + "\n\n")
    else:
      f.write("User: " + prompt + "\n\n")

  def generate():
    final = ""
    try:
      txtDir = f"uploads/{branch_name}/sessions/" + sessionToken + "/transcript.txt"
      with open(txtDir, 'a') as f:
        f.write("Coach: ")
      for chunk in client.chat.completions.create(model=model, messages=messageData, stream=True,max_tokens=max_tokens):
        content = chunk.choices[0].delta.content
        if content is not None:
          final += content
          with open(txtDir, 'a') as f:
            f.write(content)
          yield content
    except GeneratorExit:
      final += "[STOPPED BY USER]"
      with open(txtDir, 'a') as f:
        f.write("[STOPPED BY USER]")
    except Exception as e:
      print(e)
      final += "[ERROR OCCURED]"
      with open(txtDir, 'a') as f:
        f.write("[ERROR OCCURED]")
      yield "[ERROR OCCURED]"
    finally:
      messageData.append({"role": "assistant", "content": final})

      with open(jsonDir, "w") as j:
        json.dump([sessionData[0],messageData], j)

      with open(txtDir, 'a') as f:
        f.write("\n\n")

      tokensInUse.remove(sessionToken)

  if stream:
    response = Response(stream_with_context(generate()), content_type='text/plain')
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response
  else:
    try:
      content = client.chat.completions.create(model=model,messages=messageData,max_tokens=max_tokens)
      final = content.choices[0].message.content
      messageData.append({"role": "assistant", "content": final})

      with open(jsonDir, "w") as j:
        json.dump([sessionData[0],messageData], j)

      txtDir = f"uploads/{branch_name}/sessions/" + sessionToken + "/transcript.txt"
      with open(txtDir, 'a') as f:
        f.write("Coach: " + final + "\n\n")

      tokensInUse.remove(sessionToken)

      return jsonify(final)
    except:
      final = "[ERROR OCCURRED]"
      messageData.append({"role": "assistant", "content": final})

      with open(jsonDir, "w") as j:
        json.dump([sessionData[0],messageData], j)

      txtDir = f"uploads/{branch_name}/sessions/" + sessionToken + "/transcript.txt"
      with open(txtDir, 'a') as f:
        f.write("Coach: " + final + "\n\n")

      tokensInUse.remove(sessionToken)

      return jsonify(final)
