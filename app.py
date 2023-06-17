import sys, json, secrets
from flask import Flask, render_template
from flask_httpauth import HTTPBasicAuth
from flask_socketio import SocketIO, emit

app = Flask(__name__)
sock = SocketIO(app)
auth = HTTPBasicAuth()

username: str = None
msgs = []

config_file = json.loads(open("config.json").read())

@auth.verify_password
def verify_password(userid, password):
    accounts = config_file.get('accounts', {})
    if userid in accounts:
        if secrets.compare_digest(accounts.get(userid), password):
            global username
            username = userid
            return True
    return False

@app.route('/')
@auth.login_required
def login():
    return render_template('index.html', currentUser=username.capitalize())

@sock.on('get_msgs')
def send_msgs(data):
    emit("all_msgs", json.dumps(msgs))

@sock.on('message')
def handle_message(data):
    msgs.append(data)
    emit("msg", data, broadcast=True)

try:
    sock.run(app, host="0.0.0.0", port=int(sys.argv[2]))
except IndexError:
    print("USAGE: python3 app.py -p <web-port>")