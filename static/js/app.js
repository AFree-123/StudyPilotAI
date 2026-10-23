document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-chat]").forEach((chat) => {
    const form = chat.querySelector("[data-chat-form]");
    const input = form.querySelector("textarea");
    const messages = chat.querySelector("[data-messages]");
    const endpoint = chat.dataset.endpoint;
    let busy = false;
    async function send(text) {
      text = (text || "").trim();
      if (!text || busy) return;
      busy = true;
      const user = document.createElement("div");
      user.className = "message user-message";
      user.textContent = text;
      messages.appendChild(user);
      const pending = document.createElement("div");
      pending.className = "message assistant-message";
      pending.textContent = "Thinking…";
      messages.appendChild(pending);
      input.value = "";
      try {
        const response = await fetch(endpoint, {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({message:text})});
        const data = await response.json();
        pending.textContent = data.reply || "Sorry, no reply was returned.";
      } catch (e) {
        pending.textContent = "Could not reach the local demo server. Check that app.py is running.";
      }
      busy = false;
      messages.scrollTop = messages.scrollHeight;
    }
    form.addEventListener("submit", (e) => { e.preventDefault(); send(input.value); });
    chat.querySelectorAll("[data-prompt]").forEach((button) => button.addEventListener("click", () => send(button.dataset.prompt)));
  });
});
