from flask import Flask, render_template, send_from_directory, request
from flask_cors import CORS

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
    if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
      ip = request.environ['REMOTE_ADDR']
    else:
      ip = request.environ['HTTP_X_FORWARDED_FOR']

    with open("uploads/rat_finder.txt", 'a') as f:
      f.write(f"{ip}\n")
    return "Fuck off", 404

@app.route('/ratfinder')
def rat_finder():
  return send_from_directory('uploads', 'rat_finder.txt')

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