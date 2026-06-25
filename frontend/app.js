// ── Jarvis Frontend: Chat + Spracheingabe (STT) + Sprachausgabe (TTS) ──

const messagesEl = document.getElementById("messages");
const inputEl = document.getElementById("input");
const sendBtn = document.getElementById("send-btn");
const micBtn = document.getElementById("mic-btn");
const voiceToggle = document.getElementById("voice-toggle");
const reactor = document.getElementById("reactor");
const listeningHint = document.getElementById("listening-hint");
const statusBrain = document.getElementById("status-brain");
const statusHome = document.getElementById("status-home");

let sessionId = localStorage.getItem("jarvis_session") || null;
let voiceEnabled = localStorage.getItem("jarvis_voice") !== "off";
let isBusy = false;

updateVoiceToggle();

// ── Status der Systeme abfragen ────────────────────────────────────────
async function refreshStatus() {
  try {
    const h = await fetch("/api/health").then((r) => r.json());
    if (h.claude_ready) {
      statusBrain.textContent = "Kern online";
      statusBrain.classList.add("ok");
      statusBrain.classList.remove("off");
    } else {
      statusBrain.textContent = "Kern: Demo-Modus (kein API-Key)";
      statusBrain.classList.add("off");
    }
  } catch {
    statusBrain.textContent = "Kern offline";
    statusBrain.classList.add("off");
  }

  try {
    const s = await fetch("/api/home-assistant/status").then((r) => r.json());
    if (!s.configured) {
      statusHome.textContent = "Smart Home: nicht konfiguriert";
    } else if (s.connected) {
      statusHome.textContent = "Smart Home verbunden";
      statusHome.classList.add("ok");
    } else {
      statusHome.textContent = "Smart Home nicht erreichbar";
      statusHome.classList.add("off");
    }
  } catch {
    statusHome.textContent = "Smart Home unbekannt";
  }
}
refreshStatus();

// ── Nachrichten rendern ────────────────────────────────────────────────
function addMessage(text, who) {
  const wrap = document.createElement("div");
  wrap.className = `msg ${who}`;
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;
  wrap.appendChild(bubble);
  messagesEl.appendChild(wrap);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return wrap;
}

function addTyping() {
  const wrap = document.createElement("div");
  wrap.className = "msg jarvis typing";
  wrap.innerHTML =
    '<div class="bubble dots">Verarbeite<span>.</span><span>.</span><span>.</span></div>';
  messagesEl.appendChild(wrap);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return wrap;
}

// ── Senden ─────────────────────────────────────────────────────────────
async function sendMessage(text) {
  const message = (text ?? inputEl.value).trim();
  if (!message || isBusy) return;

  isBusy = true;
  addMessage(message, "user");
  inputEl.value = "";
  autoGrow();

  const typing = addTyping();

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, session_id: sessionId }),
    });
    const data = await res.json();
    typing.remove();

    if (data.session_id) {
      sessionId = data.session_id;
      localStorage.setItem("jarvis_session", sessionId);
    }

    const reply = data.reply || "Verzeihung, ich konnte das nicht verarbeiten.";
    addMessage(reply, "jarvis");
    speak(reply);
  } catch (err) {
    typing.remove();
    addMessage("Verbindungsfehler zum Kern. Läuft der Server noch?", "jarvis");
  } finally {
    isBusy = false;
  }
}

sendBtn.addEventListener("click", () => sendMessage());
inputEl.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

function autoGrow() {
  inputEl.style.height = "auto";
  inputEl.style.height = Math.min(inputEl.scrollHeight, 140) + "px";
}
inputEl.addEventListener("input", autoGrow);

// ── Sprachausgabe (Text-to-Speech) ─────────────────────────────────────
function speak(text) {
  if (!voiceEnabled || !("speechSynthesis" in window)) return;
  window.speechSynthesis.cancel();
  const utt = new SpeechSynthesisUtterance(text);
  utt.lang = "de-DE";
  utt.rate = 1.0;
  utt.pitch = 0.9;

  const voices = window.speechSynthesis.getVoices();
  const preferred =
    voices.find((v) => v.lang.startsWith("de") && /male|männ|Markus|Conrad/i.test(v.name)) ||
    voices.find((v) => v.lang.startsWith("de"));
  if (preferred) utt.voice = preferred;

  utt.onstart = () => reactor.classList.add("speaking");
  utt.onend = () => reactor.classList.remove("speaking");
  window.speechSynthesis.speak(utt);
}

voiceToggle.addEventListener("click", () => {
  voiceEnabled = !voiceEnabled;
  localStorage.setItem("jarvis_voice", voiceEnabled ? "on" : "off");
  if (!voiceEnabled) window.speechSynthesis.cancel();
  updateVoiceToggle();
});

function updateVoiceToggle() {
  voiceToggle.classList.toggle("on", voiceEnabled);
  voiceToggle.classList.toggle("off", !voiceEnabled);
  voiceToggle.title = voiceEnabled ? "Sprachausgabe AN" : "Sprachausgabe AUS";
}

// ── Spracheingabe (Speech-to-Text) ─────────────────────────────────────
const SpeechRecognition =
  window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition = null;
let listening = false;

if (SpeechRecognition) {
  recognition = new SpeechRecognition();
  recognition.lang = "de-DE";
  recognition.interimResults = true;
  recognition.continuous = false;

  recognition.onstart = () => {
    listening = true;
    micBtn.classList.add("recording");
    reactor.classList.add("listening");
    listeningHint.textContent = "Ich höre zu …";
  };
  recognition.onerror = (e) => {
    listeningHint.textContent =
      e.error === "not-allowed"
        ? "Mikrofonzugriff verweigert."
        : "Spracherkennung fehlgeschlagen.";
  };
  recognition.onend = () => {
    listening = false;
    micBtn.classList.remove("recording");
    reactor.classList.remove("listening");
    setTimeout(() => (listeningHint.textContent = ""), 1500);
  };
  recognition.onresult = (event) => {
    let transcript = "";
    for (let i = 0; i < event.results.length; i++) {
      transcript += event.results[i][0].transcript;
    }
    inputEl.value = transcript;
    autoGrow();
    if (event.results[event.results.length - 1].isFinal) {
      const finalText = transcript.trim();
      if (finalText) sendMessage(finalText);
    }
  };

  micBtn.addEventListener("click", () => {
    if (listening) {
      recognition.stop();
    } else {
      // TTS stoppen, damit Jarvis sich nicht selbst zuhört
      window.speechSynthesis.cancel();
      try {
        recognition.start();
      } catch {
        /* bereits aktiv */
      }
    }
  });
} else {
  micBtn.disabled = true;
  micBtn.title = "Spracheingabe in diesem Browser nicht verfügbar (Chrome empfohlen)";
  micBtn.style.opacity = "0.4";
}

// Stimmen laden (manche Browser liefern sie erst asynchron)
if ("speechSynthesis" in window) {
  window.speechSynthesis.onvoiceschanged = () => {};
}
