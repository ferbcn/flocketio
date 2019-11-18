import os
import time

from flask import Flask, jsonify, render_template, request, session, redirect, url_for
from flask_socketio import SocketIO, emit
from flask_session import Session

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
socketio = SocketIO(app)

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

web = {"name":"web", "users": []}
python = {"name":"python", "users": []}
fl = {"name":"flask", "users": []}
current_channels = [web, python, fl]
current_usernames = []

all_posts = []
post_id_counter = 102

for p in range(100):
    post = {"channel": "web", "user": "fer", "post": p, 'time': 'Sat Sep 21 09:14:40 2019', 'pin':'123', 'post_id':p}
    all_posts.append(post)
m1 = {"channel": "flask", "user": "fer", "post": "Lorem ipsum dolor sit amet consectetur, adipiscing elit et.", "post_id":100, 'time': 'Sat Sep 21 09:14:40 2019', 'pin':'123'}
m2 = {"channel": "python", "user": "ferX", "post": "Diam sodales turpis feugiat rhoncus inceptos per, iaculis integer tellus cubilia.", 'time': 'Sat Sep 21 09:14:40 2019', 'pin':'123', "post_id":101}
all_posts.append(m1)
all_posts.append(m2)


@app.route("/", methods=["GET", "POST"])
def login():

    channels = [channel.get("name") for channel in current_channels]

    if request.method == "GET":
    # if user logged in go directly to search page
        if session.get("username") == None:
            #user not logged in
            return render_template("login.html")
        #user is logged in
        username = session.get("username")
        if session.get("userschannel") == None:
            return render_template("list_channels.html", username=username)
        #user is logged in an in a channel
        channel_name = session.get("userschannel")
        #return render_template("channel.html", channel_name=channel_name, username=username)
        return render_template("channel.html", channel_name=channel_name, username=session["username"])

    elif request.method == "POST":

        username = request.form.get("username")
        if username in current_usernames:
            return render_template("info.html", title="Error", message="Username already in use!", link="/")
        session["username"] = username
        current_usernames.append(username)
        return render_template("list_channels.html", username=username)


@app.route("/recalluser")
def recall():

    username = request.args.get('user')
    channel = request.args.get('chname')
    print("RECALL USER: ", username, channel)

    session["username"] = username
    if channel == "null":
        session["userschannel"] = None
        return render_template("list_channels.html", username=username)
    else:
        session["userschannel"] = channel
        url = '/channel?name=' + channel
        return redirect(url)


@app.route("/logout", methods=["GET"])
def logout():
    try:
        current_usernames.remove(session["username"])
    except ValueError:
        pass
    session["username"] = None
    session["userschannel"] = None
    return render_template("info.html", title="Success", message="You are logged out!", link="/")


@app.route("/list_channels")
def list_channels():
    session["userschannel"] = None
    return render_template("list_channels.html", username=session.get("username"))

@app.route("/channels", methods=["POST"])
def channels():

    # Get start and end point for channel list to generate.
    start = int(request.form.get("start") or 0)
    end = int(request.form.get("end") or (start + 9))

    # Generate list of channels.
    channels = [channel.get("name") for channel in current_channels]
    data = channels[::-1] #invert the list of post as to show first the most recent

    # Artificially delay speed of response.
    time.sleep(0.5)

    # Return list of posts.
    return jsonify(data)


@socketio.on("create channel")
def send_channel(channel_name):

    seconds = time.time()
    local_time = time.ctime(seconds)

    ltime = local_time.split(" ")
    t = ltime[3]

    #TODO: check for existing channel name
    channel_names = [channel.get("name") for channel in current_channels]
    dict_entry = {"name": channel_name, "users":[]}

    if channel_name in channel_names:
        status = 0
    else:
        status = 1
        current_channels.append(dict_entry)

    new_channel = {"channel_name": channel_name, "time":local_time, "status":status}

    print("New channel created: ", dict_entry)
    if status == 1:
        emit("channel new", new_channel, broadcast=True)
    else:
        emit("channel new", new_channel, broadcast=False)



@app.route("/channel")
def index():
    name = request.args.get('name')
    session["userschannel"] = name
    return render_template("channel.html", channel_name=name, username=session["username"])



@app.route("/posts", methods=["POST"])
def posts():
    name = request.args.get('cname')

    # Get start and end point for posts to generate.
    start = int(request.form.get("start") or 0)
    end = int(request.form.get("end") or (start + 9))

    posts_for_channel = []
    # Generate list of posts.
    for post in all_posts:
        if post.get("channel") == name:
            if len(all_posts) >= 100:
                all_posts.pop(0)
            posts_for_channel.append(post)
    data = posts_for_channel[::-1] #invert the list of post as to show first the most recent
    # Artificially delay speed of response.
    time.sleep(0.5)
    #print(data)

    # Return list of posts.
    return jsonify(data)


@socketio.on("send message")
def send_mes(data):
    global all_posts
    global post_id_counter

    mes_rx = data["message"]
    pin = data["pin"]

    print(mes_rx, pin)

    seconds = time.time()
    local_time = time.ctime(seconds)
    ltime = local_time.split(" ")
    t = ltime[3]

    channel = session.get("userschannel")
    post_id = post_id_counter
    post_id_counter += 1

    new_post = {"channel": channel, "user": session.get("username"), "post": mes_rx, "time": local_time, "post_id": post_id}
    new_post_db = {"channel": channel, "user": session.get("username"), "post": mes_rx, "time": local_time, "pin":pin, "post_id": post_id}

    all_posts.append(new_post_db)
    print("New post appended to all_posts, id: ", post_id)

    emit("message new", new_post, broadcast=True)


@socketio.on("del message")
def del_mes(data):
    global all_posts

    mes = data["message"]
    pin = data["pin"]
    author = data["author"]
    sender = data["sender"]
    post_id = data["post_id"]
    print(mes, pin, author, sender, post_id)

    rem_post = {"mes": mes, "pin": pin, "author": author, "post_id":post_id}

    status = 0

    for post in all_posts:
        if str(post["post_id"]) == str(post_id):
            if pin == post["pin"]:
                all_posts.remove(post)
                print("Post removed !!!")
                status = 1
            else:
                print("Wrong Pin!!!")
                status = 2

    data = {"status": status, "post_id": post_id, "sender":sender}

    emit("message removed", data, broadcast=True)


if __name__== "__main__":
    app.run(debug=True, host="0.0.0.0")
