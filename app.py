from flask import Flask, render_template, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 20 * 1000 * 1000
app.config['UPLOAD_FOLDER'] = '/uploads/'
CORS(app, supports_credentials=True)

branches = ['v1']

for item in branches:
  v = __import__(item)
  app.register_blueprint(v.branch, url_prefix=f'/{v.branch_name}')

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