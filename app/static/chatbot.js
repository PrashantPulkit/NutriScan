document.addEventListener("DOMContentLoaded", () => {
    const button = document.getElementById("chatbot-button");
    const windowBox = document.getElementById("chatbot-window");
    const closeBtn = document.getElementById("close-chatbot");
    const form = document.getElementById("chatbot-form");
    const input = document.getElementById("chatbot-input");
    const messages = document.getElementById("chatbot-messages");
  
    // Toggle chatbot window
    button.addEventListener("click", () => {
      windowBox.classList.toggle("hidden");
    });
  
    closeBtn.addEventListener("click", () => {
      windowBox.classList.add("hidden");
    });
  
    // Send message
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const userText = input.value.trim();
      if (!userText) return;
  
      addMessage("user", userText);
      input.value = "";
  
      const response = await fetch("/chatbot", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userText }),
      });
  
      const data = await response.json();
      addMessage("bot", data.reply);
    });
  
    function addMessage(sender, text) {
      const msg = document.createElement("div");
      msg.classList.add("message");
      msg.classList.add(sender === "user" ? "user-message" : "bot-message");
      msg.innerText = text;
      messages.appendChild(msg);
      messages.scrollTop = messages.scrollHeight;
    }
  });
  