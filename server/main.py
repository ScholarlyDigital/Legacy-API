from flask import Flask, jsonify, render_template, send_from_directory
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app, supports_credentials=True)

@app.route('/openai',methods=['GET'])
def openai():
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
  
app.run(host='0.0.0.0')
