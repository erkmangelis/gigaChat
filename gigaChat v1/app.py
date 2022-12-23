from flask import Flask, render_template, flash, redirect, request, session, url_for
from flask_socketio import SocketIO, emit
from cs50 import SQL
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime


app = Flask(__name__)
app.config["SECRET_KEY"] = "erkman"
# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True
socket = SocketIO(app)

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///chatApp.db")

# Chat history
history = []

# Online Users
online = []

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Redecirt to index
@app.route("/")
def index():
    if session.get("username") is None:
        return render_template("index.html")
    else:
        deneme = session.get("username")
        return render_template("chat.html", susername=session.get("username"))

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    
    # Forget any username
    session.clear()
    
    status=""
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            status="usr"
            flash("Username cannot be empty")
            return render_template("login.html", status=status)

        # Ensure password was submitted
        if not request.form.get("password"):
            status="pass"
            flash("Password cannot be empty")
            return render_template("login.html", status=status)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            status="usrpass"
            flash("Wrong username or password")
            return render_template("login.html", status=status)

         # Remember which user has logged in
        session["username"] = rows[0]["username"]

        # Redirect user to chat page
        return redirect("/")
        
    # User reached route via GET
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any username
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "GET":
        return render_template("register.html")
    # check username and password
    
    status=""
    username = request.form.get("username")
    password = request.form.get("password")
    confirmation = request.form.get("confirmation")
    if username == "" or len(db.execute('SELECT username FROM users WHERE username = ?', username)) > 0:
        status="usr"
        flash("Invalid Username: Blank or already exists")
        return render_template("register.html", status=status)
    if password == "" or password != confirmation:
        status="pass"
        flash("Invalid Password: Blank or does not match")
        return render_template("register.html", status=status)

    # Add new user to users db
    db.execute('INSERT INTO users (username, hash) VALUES(?, ?)', username, generate_password_hash(password))
    # Query database for username
    rows = db.execute("SELECT * FROM users WHERE username = ?", username)
    # Log user in, i.e. Remember that this user has logged in
    session["username"] = rows[0]["username"]
    # Redirect user to home page
    return redirect("/")


#################### SocketIO Part ####################

# User Disconnect Messages
@socket.on('disconnect')
def sayBye():
    global online
    username = session.get("username")
    message = username.capitalize() + " has disconnected"
    time = str(datetime.now().time().strftime("%H:%M"))
    online.remove(username.capitalize())
    data = {"username":"SYSTEM:", "message":message, "time":time, "online":online}
    socket.send(data)
    

# User Connect Messages
@socket.on('connect')
def sayHi():
    global online
    username = session.get("username")
    message = username.capitalize() + " has connected"
    time = str(datetime.now().time().strftime("%H:%M"))
    online.append(username.capitalize())
    data = {"username":"SYSTEM:", "message":message, "time":time, "sender":username, "history":history, "online":online}
    socket.send(data)
    
    
# Sending messages to clients that received from user
@socket.on('message')
def handleMessage(message):
    global history
    if message != "/clear":
        username = session.get("username").capitalize() + ":"
        time = str(datetime.now().time().strftime("%H:%M"))
        data = {"username":username, "message":message, "time":time, "online":online}
        socket.send(data)
        history.append(data)
    else:
        history = []
        username = session.get("username").capitalize()
        message = "Chat history cleared by " + username + ". New joiners won't be able to see old messages."
        time = str(datetime.now().time().strftime("%H:%M"))
        data = {"username":"SYSTEM:", "message":message, "time":time, "online":online}
        socket.send(data)


if __name__ == "__main__":
    socket.run(app)
