document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("voiceForm");
  const input = document.getElementById("voiceInput");
  const chat = document.getElementById("voiceChat");
  const mic = document.getElementById("micButton");
  const status = document.getElementById("voiceStatus");
  let busy = false;
  async function send(text) {
    text = (text || "").trim();
    if (!text || busy) return;
    busy = true;
    const user = document.createElement("div");
    user.className = "voice-user"; user.textContent = text; chat.appendChild(user);
    const reply = document.createElement("div");
    reply.className = "voice-reply"; reply.textContent = "One moment…"; chat.appendChild(reply);
    input.value = "";
    try {
      const response = await fetch("/alexa-demo/chat", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({message:text})});
      const data = await response.json(); reply.textContent = data.reply || "No response returned.";
    } catch (_) { reply.textContent = "Could not reach the demo server. Make sure app.py is running."; }
    busy = false;
  }
  form.addEventListener("submit", e => { e.preventDefault(); send(input.value); });
  document.querySelectorAll("[data-voice-prompt]").forEach(btn => btn.addEventListener("click", () => send(btn.dataset.voicePrompt)));
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    mic.addEventListener("click", () => { status.textContent = "This browser does not support speech recognition. Please use Chrome or Edge, or type your question."; });
    return;
  }
  const recognition = new SpeechRecognition();
  recognition.lang = "en-IN"; recognition.interimResults = false; recognition.maxAlternatives = 1;
  recognition.onstart = () => { mic.classList.add("listening"); status.textContent = "Listening… speak now."; };
  recognition.onend = () => mic.classList.remove("listening");
  recognition.onerror = e => { mic.classList.remove("listening"); status.textContent = "Microphone issue: " + e.error + ". Check browser permission or type instead."; };
  recognition.onresult = e => { input.value = e.results[0][0].transcript; status.textContent = "Voice converted to text. Press send to submit."; input.focus(); };
  mic.addEventListener("click", () => { try { recognition.start(); } catch (_) { status.textContent = "Already listening. Please finish speaking."; } });
});
