import eventlet
eventlet.monkey_patch()

import os
import resend

from flask import Flask, render_template, redirect, url_for, request, flash
from flask_socketio import SocketIO, join_room, leave_room, emit
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer

from models import db, User, Room, Message

# ─────────────────────────────────────────────
# EMAIL (Resend)
# ─────────────────────────────────────────────
resend.api_key = os.environ.get("RESEND_API_KEY")

def send_verification_email(email, link):
    resend.Emails.send({
        "from": "Campus Connect <onboarding@resend.dev>",
        "to": email,
        "subject": "Verify your account",
        "html": f"""
            <h2>Verify your account</h2>
            <p>Click the link below:</p>
            <a href="{link}">{link}</a>
        """
    })

# ─────────────────────────────────────────────
# APP SETUP
# ─────────────────────────────────────────────
app = Flask(__name__)
app.config["SECRET_KEY"] = "campus-connect-secret"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

socketio = SocketIO(app, async_mode="eventlet", cors_allowed_origins="*")

login_manager = LoginManager(app)
login_manager.login_view = "login"

serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])

# ─────────────────────────────────────────────
# USER LOADER
# ─────────────────────────────────────────────
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ─────────────────────────────────────────────
# TOKEN HELPERS
# ─────────────────────────────────────────────
def generate_token(email):
    return serializer.dumps(email, salt="email-confirm")

def confirm_token(token):
    return serializer.loads(token, salt="email-confirm", max_age=3600)

# ─────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────

@app.route("/")
def index():
    return redirect(url_for("login"))

# ─── REGISTER ────────────────────────────────
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        if User.query.filter_by(email=email).first():
            flash("Email already exists")
            return redirect(url_for("register"))

        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            is_verified=False
        )

        db.session.add(user)
        db.session.commit()

        # create verification link
        token = generate_token(user.email)

        link = url_for("verify_email", token=token, _external=True)

        # SEND EMAIL (REAL)
        send_verification_email(user.email, link)

        flash("Check your email for verification link")
        return redirect(url_for("login"))

    return render_template("register.html")

# ─── VERIFY EMAIL ────────────────────────────
@app.route("/verify/<token>")
def verify_email(token):

    try:
        email = confirm_token(token)
    except:
        return "Invalid or expired link"

    user = User.query.filter_by(email=email).first()

    if not user:
        return "User not found"

    user.is_verified = True
    db.session.commit()

    return "Email verified! You can now login."

# ─── LOGIN ───────────────────────────────────
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        if not user:
            flash("Invalid login")
            return redirect(url_for("login"))

        if not user.is_verified:
            flash("Please verify your email first")
            return redirect(url_for("login"))

        if check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for("dashboard"))

        flash("Wrong password")

    return render_template("login.html")

# ─── DASHBOARD ───────────────────────────────
@app.route("/dashboard")
@login_required
def dashboard():
    rooms = Room.query.all()
    return render_template("dashboard.html", rooms=rooms)

# ─── CREATE ROOM ─────────────────────────────
@app.route("/create-room", methods=["POST"])
@login_required
def create_room():

    name = request.form["name"]

    room = Room(name=name, created_by=current_user.id)
    db.session.add(room)
    db.session.commit()

    return redirect(url_for("dashboard"))

# ─── ROOM PAGE ───────────────────────────────
@app.route("/room/<int:room_id>")
@login_required
def room(room_id):

    room = Room.query.get(room_id)
    messages = Message.query.filter_by(room_id=room_id).all()

    return render_template("room.html", room=room, messages=messages)

# ─────────────────────────────────────────────
# SOCKET EVENTS
# ─────────────────────────────────────────────

@socketio.on("join")
def join(data):
    join_room(str(data["room_id"]))

@socketio.on("leave")
def leave(data):
    leave_room(str(data["room_id"]))

@socketio.on("message")
def message(data):

    msg = Message(
        content=data["content"],
        user_id=current_user.id,
        room_id=int(data["room_id"])
    )

    db.session.add(msg)
    db.session.commit()

    emit("message", {
        "content": data["content"],
        "username": current_user.username
    }, to=str(data["room_id"]))

# ─────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────
if __name__ == "__main__":

    with app.app_context():
        db.create_all()

    socketio.run(app, host="0.0.0.0", port=5000)