<<<<<<< HEAD
# 🎓 Campus Connect
### University Real-Time Chat Platform

A clean, minimal, and fully functional real-time chat application for university students built with **Flask + Socket.IO**.

---

## ✨ Features

| Feature | Details |
|---|---|
| 🔐 Authentication | Register, Login, Logout with password hashing |
| 💬 Real-Time Chat | Instant messaging via Socket.IO WebSockets |
| 🏠 Study Rooms | Create and join named chat rooms |
| 👥 Online Users | Live online/offline indicator in sidebar |
| 📱 Responsive UI | Works on desktop and mobile |
| 💾 Persistence | All messages saved to SQLite database |

---

## 🗂 Project Structure

```
campus_connect/
│
├── app.py              # Flask app, routes, Socket.IO events
├── models.py           # SQLAlchemy database models
├── requirements.txt    # Python dependencies
├── setup.sh            # One-click setup & run script
│
├── templates/
│   ├── login.html      # Login page
│   ├── register.html   # Registration page
│   ├── dashboard.html  # Room list + create room
│   └── room.html       # Real-time chat room
│
└── static/
    ├── style.css       # All styles (dark academic theme)
    └── chat.js         # Socket.IO client logic
```

---

## ⚙️ Tech Stack

**Backend**
- Python 3.10+
- Flask 3.x
- Flask-SocketIO (WebSocket events)
- Flask-SQLAlchemy (ORM)
- Flask-Login (session management)
- SQLite (database)
- Eventlet (async worker)

**Frontend**
- Pure HTML5
- Custom CSS (CSS Variables, dark theme)
- Vanilla JavaScript
- Socket.IO client (CDN)
- Google Fonts: Sora + JetBrains Mono

---

## 🚀 Quick Start

### Option A — Setup Script (recommended)

```bash
cd campus_connect
chmod +x setup.sh
./setup.sh
```

### Option B — Manual

```bash
# 1. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
python app.py
```

Then open **http://127.0.0.1:5000** in your browser.

---

## 📋 How to Use

1. **Register** a new account at `/register`
2. **Login** at `/login`
3. On the **Dashboard**, you'll see all available study rooms
4. **Join** any room to start chatting in real time
5. **Create** your own room using the "+ New Room" button
6. Online users are visible in the **left sidebar**

---

## 🗄️ Database Models

### User
| Field | Type | Description |
|---|---|---|
| id | Integer | Primary key |
| username | String(80) | Unique username |
| email | String(120) | Unique email |
| password_hash | String(256) | Hashed password |
| is_online | Boolean | Online status flag |

### Room
| Field | Type | Description |
|---|---|---|
| id | Integer | Primary key |
| name | String(100) | Unique room name |
| description | String(255) | Optional description |
| created_by | FK → User | Creator |

### Message
| Field | Type | Description |
|---|---|---|
| id | Integer | Primary key |
| content | Text | Message body |
| timestamp | DateTime | When sent |
| user_id | FK → User | Author |
| room_id | FK → Room | Destination room |

---

## 🔌 Socket.IO Events

| Event | Direction | Description |
|---|---|---|
| `join` | Client → Server | Join a room |
| `leave` | Client → Server | Leave a room |
| `send_message` | Client → Server | Send a message |
| `new_message` | Server → Client | Broadcast new message |
| `status` | Server → Client | System notifications |

---

## 🎨 Design Notes

- **Theme**: Dark academic — deep navy backgrounds, teal accents
- **Fonts**: Sora (UI) + JetBrains Mono (timestamps, codes)
- **Animations**: Subtle message slide-in, floating orbs on auth pages
- **Colors**: `#0d0f14` background · `#2dd4bf` teal accent · `#6366f1` purple highlight

---

## 📦 Dependencies

```
Flask==3.0.3
Flask-SocketIO==5.3.6
Flask-SQLAlchemy==3.1.1
Flask-Login==0.6.3
Werkzeug==3.0.3
python-socketio==5.11.3
python-engineio==4.9.1
eventlet==0.36.1
```

---

*Built as a university semester project demonstrating real-time web communication with Flask and Socket.IO.*
=======
# Campus_Connect
>>>>>>> 6afa3036f04f3aceb5cac95ef893284d84571c2e
