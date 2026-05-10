/**
 * Campus Connect — Chat Client
 * Handles real-time messaging via Socket.IO
 */

(function () {
  "use strict";

  // ── Read server-injected data ──────────────────────────────
  const chatData   = document.getElementById("chat-data");
  const ROOM_ID    = chatData.dataset.roomId;
  const USERNAME   = chatData.dataset.username;
  const USER_ID    = parseInt(chatData.dataset.userId, 10);

  // ── DOM refs ───────────────────────────────────────────────
  const messagesEl = document.getElementById("messages");
  const inputEl    = document.getElementById("msg-input");
  const sendBtn    = document.getElementById("send-btn");

  // ── Connect to Socket.IO ───────────────────────────────────
  const socket = io({ transports: ["websocket", "polling"] });

  socket.on("connect", function () {
    socket.emit("join", { room_id: ROOM_ID });
  });

  socket.on("disconnect", function () {
    appendSystem("⚠ Connection lost. Reconnecting…");
  });

  socket.on("connect_error", function () {
    appendSystem("⚠ Could not connect to server.");
  });

  // ── Receive messages ───────────────────────────────────────
  socket.on("new_message", function (data) {
    const isSelf = data.user_id === USER_ID;
    appendMessage(data, isSelf);
    scrollToBottom();
  });

  socket.on("status", function (data) {
    appendSystem(data.msg);
  });

  // ── Send message ───────────────────────────────────────────
  function sendMessage() {
    const content = inputEl.value.trim();
    if (!content) return;

    socket.emit("send_message", {
      room_id: ROOM_ID,
      content: content,
    });

    inputEl.value = "";
    inputEl.style.height = "auto";
    inputEl.focus();
  }

  sendBtn.addEventListener("click", sendMessage);

  inputEl.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  // Auto-grow textarea
  inputEl.addEventListener("input", function () {
    this.style.height = "auto";
    this.style.height = Math.min(this.scrollHeight, 120) + "px";
  });

  // ── DOM helpers ────────────────────────────────────────────
  function appendMessage(data, isSelf) {
    const wrapper = document.createElement("div");
    wrapper.classList.add("msg", isSelf ? "msg-self" : "msg-other");

    if (isSelf) {
      wrapper.innerHTML = `
        <div class="msg-bubble">
          <p class="msg-text">${escapeHtml(data.content)}</p>
          <span class="msg-time">${data.timestamp}</span>
        </div>`;
    } else {
      const initial = data.username.charAt(0).toUpperCase();
      wrapper.innerHTML = `
        <span class="msg-avatar">${escapeHtml(initial)}</span>
        <div>
          <span class="msg-username">${escapeHtml(data.username)}</span>
          <div class="msg-bubble">
            <p class="msg-text">${escapeHtml(data.content)}</p>
            <span class="msg-time">${data.timestamp}</span>
          </div>
        </div>`;
    }

    messagesEl.appendChild(wrapper);
  }

  function appendSystem(text) {
    const el = document.createElement("div");
    el.className = "msg-system";
    el.textContent = text;
    messagesEl.appendChild(el);
    scrollToBottom();
  }

  function scrollToBottom() {
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function escapeHtml(str) {
    const d = document.createElement("div");
    d.textContent = str;
    return d.innerHTML;
  }

  // Scroll on load
  scrollToBottom();

  // Leave room on page unload
  window.addEventListener("beforeunload", function () {
    socket.emit("leave", { room_id: ROOM_ID });
  });

})();
