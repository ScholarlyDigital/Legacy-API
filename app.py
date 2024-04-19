from flask import Flask, render_template, send_from_directory, request
from flask_cors import CORS
import json

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 20 * 1000 * 1000
app.config['UPLOAD_FOLDER'] = '/uploads/'
CORS(app, supports_credentials=True)

branches = ['v1']

for item in branches:
  v = __import__(item)
  app.register_blueprint(v.branch, url_prefix=f'/{v.branch_name}')

@app.errorhandler(404)
def page_not_found(e):
  
  ip = request.headers.get('X-Forwarded-For', request.remote_addr)
  headers = dict(request.headers)
  cookies = request.cookies.to_dict()
  query_params = request.args.to_dict()
  json_payload = request.get_json(silent=True)
  request_method = request.method
  full_request_path = request.full_path

  client_data = {
    "IP": ip,
    "Headers": headers,
    "Cookies": cookies,
    "Query Parameters": query_params,
    "JSON Payload": json_payload,
    "Request Method": request_method,
    "Full Request Path": full_request_path
  }

  with open("uploads/ratfinder.json", 'a') as f:
    json.dump(client_data, f)
    f.write('\n')

  return "Fuck off", 404

@app.route('/ratfinder')
def rat_finder():
  return send_from_directory('uploads', 'ratfinder.json')

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

if __name__ == "__main__":
  app.run(host='0.0.0.0', port=80, threaded=True)