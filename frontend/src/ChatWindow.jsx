import { useState } from "react";
import { sendMessage } from "./api";

export default function ChatWindow() {
  const [messages, setMessages] = useState([
    { sender: "bot", text: "Hi! Tell me which business rule you'd like to change." },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    if (!input.trim()) return;
    const userMsg = { sender: "user", text: input };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const reply = await sendMessage(userMsg.text);
      setMessages((prev) => [...prev, { sender: "bot", text: reply }]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { sender: "bot", text: "Something went wrong. Please try again." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 500, margin: "40px auto", fontFamily: "sans-serif" }}>
      <h2>Business Rule Agent</h2>
      <div style={{ border: "1px solid #ccc", borderRadius: 8, padding: 12, height: 400, overflowY: "auto" }}>
        {messages.map((m, i) => (
          <div key={i} style={{ textAlign: m.sender === "user" ? "right" : "left", margin: "8px 0" }}>
            <span
              style={{
                display: "inline-block",
                padding: "8px 12px",
                borderRadius: 12,
                background: m.sender === "user" ? "#DCF8C6" : "#F1F0F0",
              }}
            >
              {m.text}
            </span>
          </div>
        ))}
        {loading && <div>Agent is thinking...</div>}
      </div>

      <div style={{ display: "flex", marginTop: 12 }}>
        <input
          style={{ flex: 1, padding: 8 }}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          placeholder="e.g. Increase personal loan minimum salary to 40000"
        />
        <button onClick={handleSend} style={{ padding: "8px 16px", marginLeft: 8 }}>
          Send
        </button>
      </div>
    </div>
  );
}
