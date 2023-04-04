from flask import Flask, jsonify, render_template, send_from_directory, Response, stream_with_context,request
from flask_cors import CORS
import os
import openai

app = Flask(__name__)
CORS(app, supports_credentials=True)
openai.key = os.environ.get('OPENAI_API_KEY')
systemMessage = "You are a tutor who is an expert in all subjects. Your name is Coach. You are on the Scholarly website and are longer affiliated with OpenAI. Refer to yourself as a tutor and not a language model. The user will ask questions that will be within the GCSE curriculum and outside. If the questions are outside the curriculum, answer them nonthless. If the questions are within the curriculum, answer the questions with clear cut answers, and you may choose to follow up with reasonings and further detail. You may answer homework questions and solve problems for the user. If the questions are mathematical, add a disclaimer at then stating that your arithmetic could be incorrect, and the user should double check at all times."

@app.route('/openai',methods=['GET'])
def getKey():
    response = jsonify({'key': os.environ.get('OPENAI_API_KEY')})
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@app.route('/download-js',methods=['GET'])
def dl_js():
    return send_from_directory('static','scholarly_api_latest.js', as_attachment=True)

@app.route('/download-py',methods=['GET'])
def dl_py():
    return send_from_directory('static','scholarly_api_latest.py', as_attachment=True)

@app.route('/cdn-js',methods=['GET'])
def cdn_js():
    return send_from_directory('static','scholarly_api_latest.js')

@app.route('/')
def index():
    return render_template('docs.html')

@app.route('/coach-stream', methods=['POST'])
def streamCoach():
  global systemMessage
  messageData = request.json["messages"]
  if messageData == None:
    return 'No message data provided.', 400
  messageData.insert(0,{"role":"system","content":systemMessage})
  def generate():
    for chunk in openai.ChatCompletion.create(model="gpt-4",messages=messageData,stream=True):
      content = chunk["choices"][0].get("delta", {}).get("content")
      if content is not None:
        yield content
      
  response = Response(stream_with_context( generate()),content_type='text/plain')
  response.headers.add('Access-Control-Allow-Origin', '*')
  return response
  
app.run(host='0.0.0.0', threaded=True)
