from flask import Flask, render_template
from flask_httpauth import HTTPBasicAuth
from flask_socketio import SocketIO, emit
import sys, requests, json

app = Flask(__name__)
sock = SocketIO(app)
auth = HTTPBasicAuth()

user = None
user_sock = {}
msgs = []
active = {}

config_file = json.loads(open("config.json").read())

@auth.verify_password
def verify_password(email, password):
    return verifyAuthentication(email, password)
def verifyAuthentication(email, password):
    knownUsers = config_file['accounts']
    authenticated = False
    if email in knownUsers:
        if knownUsers[email] == password:
            global user
            user = email
            authenticated = True
    return authenticated

@app.route('/')
@auth.login_required
def login():
    receiver = config_file['accounts'].copy()
    del receiver[user]
    return render_template('index.html', name=user, receiver=[x for x in receiver][0])

@sock.on('get_msgs')
def send_msgs(data):
    active[data['user']] = "Online"
    for x in msgs:
        emit("msg", x)
    emit('ping_client', {})

@sock.on('message')
def handle_message(data):
    msgs.append(data)
    emit("msg", data, broadcast=True)

@sock.on('type')
def handle_typing(data):
    emit("typing", data, broadcast=True)

@sock.on('ping')
def handle_ping(data):
    active[data['user']] = "Online"
    emit('active_users', active, broadcast=True)

@sock.on('webhook')
def handle_webhook(data):
    if config_file['discord_webhook']['hook_url'] != None:
        requests.post(config_file['discord_webhook']['hook_url'], headers = {'Content-Type': 'application/json'}, data = json.dumps({"username":config_file['discord_webhook']['username'], "content": data, "avatar_url":config_file['discord_webhook']['avatar_url']}))

@sock.on('disconnect')
def handle_disconnect():
    for x in active:
        active[x] = "Offline"
    emit("ping_client", {}, broadcast=True)

try:
    sock.run(app, host="0.0.0.0", port=int(sys.argv[2]))
except IndexError:
    print("USAGE: python3 app.py -p <web-port>")