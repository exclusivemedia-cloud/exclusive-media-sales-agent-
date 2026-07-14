"use client";

import { useState } from "react";
import type { ChatMessage } from "@/lib/db";

const GENERIC_REPLIES = [
  "Got it — let me check availability for you. What's your service zip code?",
  "Understood. I've logged that for the team. Would tomorrow morning work for a visit?",
  "Thanks for the details! I can get you booked in — what's the best number to text you at?",
];

export default function AiOpsChatSandbox({
  businessName,
  script,
}: {
  businessName: string;
  script: ChatMessage[];
}) {
  const [messages, setMessages] = useState<ChatMessage[]>(script);
  const [input, setInput] = useState("");
  const [replyIndex, setReplyIndex] = useState(0);

  function handleSend() {
    const text = input.trim();
    if (!text) return;
    setMessages((prev) => [...prev, { sender: "customer", text }]);
    setInput("");

    setTimeout(() => {
      const reply = GENERIC_REPLIES[replyIndex % GENERIC_REPLIES.length];
      setReplyIndex((i) => i + 1);
      setMessages((prev) => [...prev, { sender: "ai", text: reply }]);
    }, 900);
  }

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-3xl shadow-2xl overflow-hidden">
      <div className="bg-slate-950 p-4 border-b border-slate-800 flex items-center space-x-3">
        <div className="bg-emerald-500 text-slate-950 h-8 w-8 rounded-full flex items-center justify-center">
          <span className="material-icons text-sm">android</span>
        </div>
        <div>
          <h4 className="text-sm font-semibold text-white">
            {businessName} AI Assistant
          </h4>
          <span className="text-[10px] text-emerald-400 font-mono flex items-center">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 mr-1" />
            Live demo — try it yourself
          </span>
        </div>
      </div>

      <div className="p-4 space-y-2.5 max-h-[320px] overflow-y-auto">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={msg.sender === "customer" ? "flex justify-start" : "flex justify-end"}
          >
            <div
              className={
                msg.sender === "customer"
                  ? "bg-slate-800 text-slate-200 text-xs px-3.5 py-2.5 rounded-2xl max-w-[85%] rounded-tl-none"
                  : "bg-emerald-500 text-slate-950 text-xs font-medium px-3.5 py-2.5 rounded-2xl max-w-[85%] rounded-tr-none"
              }
            >
              {msg.text}
            </div>
          </div>
        ))}
      </div>

      <div className="flex space-x-2 p-4 border-t border-slate-800">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          placeholder="Type a mock customer question..."
          className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
        />
        <button
          onClick={handleSend}
          className="bg-emerald-500 text-slate-950 px-3 rounded-xl flex items-center justify-center hover:bg-emerald-400"
        >
          <span className="material-icons text-sm">send</span>
        </button>
      </div>
    </div>
  );
}
