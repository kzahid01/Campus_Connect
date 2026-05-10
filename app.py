import eventlet
eventlet.monkey_patch()
import resend
import os

resend.api_key = os.environ.get("RESEND_API_KEY")

def send_verification_email(email, link):
    resend.Emails.send({
        "from": "Campus Connect <onboarding@resend.dev>",
        "to": email,
        "subject": "Verify your account",
        "html": f"""
            <h2>Verify your account</h2>
            <p>Click this link:</p>
            <a href="{link}">{link}</a>
        """
    })

from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_socketio import SocketIO, join_room, leave_room, emit
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer
from models import db, User, Room, Message

# ── App Configuration ─────────────────────────────────────────────────────────
app = Flask(__name__)
app.config["SECRET_KEY"] = "campus-connect-secret-key-2024"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# ── Extensions ────────────────────────────────────────────────────────────────
db.init_app(app)
socketio = SocketIO(app, async_mode="eventlet", cors_allowed_origins="*")
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Please log in to access Campus Connect."

# ── Email Verification Token ─────────────────────────────────────────────────
serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])


def generate_token(email):
    return serializer.dumps(email, salt="email-confirm")


def confirm_token(token, expiration=3600):
    return serializer.loads(
        token,
        salt="email-confirm",
        max_age=expiration
    )


# ── Login Manager ─────────────────────────────────────────────────────────────
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ══════════════════════════════════════════════════════════════════════════════
#  AUTH ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        # Validation
        if not username or not email or not password:
            flash("All fields are required.", "error")
            return render_template("register.html")

        if len(username) < 3:
            flash("Username must be at least 3 characters.", "error")
            return render_template("register.html")

        if password != confirm:
            flash("Passwords do not match.", "error")
            return render_template("register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
            return render_template("register.html")

        if User.query.filter_by(username=username).first():
            flash("Username already taken.", "error")
            return render_template("register.html")

        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "error")
            return render_template("register.html")

        # Create user
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            is_verified=False
        )

        db.session.add(user)
        db.session.commit()

        # ── Generate Verification Link ─────────────────────────
        token = generate_token(user.email)

        verification_link = url_for(
            "verify_email",
            token=token,
            _external=True
        )

        print("\n=== EMAIL VERIFICATION LINK ===")
        print(verification_link)
        print("================================\n")

        flash(
            "Account created! Check terminal for verification link.",
            "success"
        )

        return redirect(url_for("login"))

    return render_template("register.html")


# ── VERIFY EMAIL ──────────────────────────────────────────────────────────────
@app.route("/verify/<token>")
def verify_email(token):

    try:
        email = confirm_token(token)

    except Exception:
        return "❌ Verification link invalid or expired."

    user = User.query.filter_by(email=email).first()

    if not user:
        return "User not found."

    if user.is_verified:
        return "✅ Account already verified."

    user.is_verified = True
    db.session.commit()

    return "✅ Email verified successfully! You can now log in."


@app.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()

        if not user:
            flash("Invalid username or password.", "error")
            return render_template("login.html")

        # ✅ REMOVED EMAIL VERIFICATION CHECK

        if check_password_hash(user.password_hash, password):

            user.is_online = True
            db.session.commit()

            login_user(user, remember=True)

            return redirect(url_for("dashboard"))

        else:
            flash("Invalid username or password.", "error")

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    current_user.is_online = False
    db.session.commit()
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


# ══════════════════════════════════════════════════════════════════════════════
#  DASHBOARD ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/dashboard")
@login_required
def dashboard():
    rooms = Room.query.order_by(Room.created_at.desc()).all()
    online_users = User.query.filter_by(is_online=True).all()
    return render_template("dashboard.html", rooms=rooms, online_users=online_users)


@app.route("/create-room", methods=["POST"])
@login_required
def create_room():
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()

    if not name:
        flash("Room name is required.", "error")
        return redirect(url_for("dashboard"))

    if len(name) < 3:
        flash("Room name must be at least 3 characters.", "error")
        return redirect(url_for("dashboard"))

    if Room.query.filter_by(name=name).first():
        flash("A room with that name already exists.", "error")
        return redirect(url_for("dashboard"))

    room = Room(
        name=name,
        description=description,
        created_by=current_user.id
    )

    db.session.add(room)
    db.session.commit()

    flash(f'Room "{name}" created!', "success")

    return redirect(url_for("room", room_id=room.id))


# ══════════════════════════════════════════════════════════════════════════════
#  ROOM ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/room/<int:room_id>")
@login_required
def room(room_id):
    room = Room.query.get_or_404(room_id)

    messages = Message.query.filter_by(
        room_id=room_id
    ).order_by(
        Message.timestamp.asc()
    ).limit(100).all()

    online_users = User.query.filter_by(is_online=True).all()

    return render_template(
        "room.html",
        room=room,
        messages=messages,
        online_users=online_users
    )
@app.route("/delete-room/<int:room_id>", methods=["POST"])
@login_required
def delete_room(room_id):

    room = Room.query.get_or_404(room_id)

    # optional: only allow creator or admin
    if room.created_by != current_user.id:
        flash("Not allowed", "error")
        return redirect(url_for("dashboard"))

    # delete messages first (important)
    Message.query.filter_by(room_id=room_id).delete()

    db.session.delete(room)
    db.session.commit()

    flash("Room deleted", "success")
    return "deleted"
@app.route("/delete-message/<int:msg_id>", methods=["POST"])
@login_required
def delete_message(msg_id):

    msg = Message.query.get_or_404(msg_id)

    # only owner can delete
    if msg.user_id != current_user.id:
        return "Not allowed", 403

    db.session.delete(msg)
    db.session.commit()

    return "Deleted"

# ══════════════════════════════════════════════════════════════════════════════
#  SOCKET.IO EVENTS
# ══════════════════════════════════════════════════════════════════════════════

@socketio.on("join")
def on_join(data):

    room_id = str(data.get("room_id"))

    join_room(room_id)

    emit(
        "status",
        {
            "msg": f"{current_user.username} joined the room.",
            "username": "System"
        },
        to=room_id
    )


@socketio.on("leave")
def on_leave(data):

    room_id = str(data.get("room_id"))

    leave_room(room_id)

    emit(
        "status",
        {
            "msg": f"{current_user.username} left the room.",
            "username": "System"
        },
        to=room_id
    )


@socketio.on("send_message")
def handle_message(data):

    room_id = data.get("room_id")
    content = data.get("content", "").strip()

    if not content or not room_id:
        return

    # Truncate very long messages
    content = content[:1000]

    # Save to database
    message = Message(
        content=content,
        user_id=current_user.id,
        room_id=int(room_id),
    )

    db.session.add(message)
    db.session.commit()

    # Broadcast to room
    emit(
        "new_message",
        {
            "id": message.id,
            "content": content,
            "username": current_user.username,
            "user_id": current_user.id,
            "timestamp": message.timestamp.strftime("%H:%M · %b %d"),
            "is_self": False,
        },
        to=str(room_id)
    )


@socketio.on("connect")
def on_connect():

    if current_user.is_authenticated:
        current_user.is_online = True
        db.session.commit()


@socketio.on("disconnect")
def on_disconnect():

    if current_user.is_authenticated:
        current_user.is_online = False
        db.session.commit()


# ══════════════════════════════════════════════════════════════════════════════
#  DB INIT & SEED
# ══════════════════════════════════════════════════════════════════════════════

def seed_default_rooms():
    """Create a few default rooms if none exist."""

    if Room.query.count() == 0:

        admin = User.query.first()

        if not admin:
            return

        defaults = [
            ("General 📢", "Open chat for all students"),
            ("CS Study Group 💻", "Computer Science discussions"),
            ("Math Help 📐", "Mathematics study & problem solving"),
            ("Off Topic 🎮", "Anything goes — games, memes, fun"),
        ]

        for name, desc in defaults:

            room = Room(
                name=name,
                description=desc,
                created_by=admin.id
            )

            db.session.add(room)

        db.session.commit()


if __name__ == "__main__":

    with app.app_context():
        db.create_all()
        seed_default_rooms()

    print("\n🎓 Campus Connect is running!")
    print("http://127.0.0.1:5000\n")

    socketio.run(
        app,
        debug=True,
        host="0.0.0.0",
        port=5000
    )