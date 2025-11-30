"use client";

import { useState } from "react";

type Source = { file_name: string; page: number };

type DoorItem = {
  mark: string;
  location: string;
  width_mm?: number | null;
  height_mm?: number | null;
  fire_rating?: string | null;
  material?: string | null;
  source_file?: string;
  source_page?: number;
};

type Message =
  | { role: "user"; content: string }
  | {
      role: "assistant";
      type: "qa";
      content: string;
      sources: Source[];
    }
  | {
      role: "assistant";
      type: "structured";
      content: string;
      data: DoorItem[];
      sources: Source[];
    };

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!input.trim()) return;
    const userMsg: Message = { role: "user", content: input };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: input }),
      });
      const data = await res.json();
      if (data.type === "structured") {
        const assistantMsg: Message = {
          role: "assistant",
          type: "structured",
          content: "Here is the door schedule I found:",
          data: data.data || [],
          sources: data.sources || [],
        };
        setMessages((prev) => [...prev, assistantMsg]);
      } else {
        const assistantMsg: Message = {
          role: "assistant",
          type: "qa",
          content: data.answer,
          sources: data.sources || [],
        };
        setMessages((prev) => [...prev, assistantMsg]);
      }
    } catch (e) {
      const errorMsg: Message = {
        role: "assistant",
        type: "qa",
        content: "Error contacting backend",
        sources: [],
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
      setInput("");
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-black text-white p-4">
      <h1 className="text-2xl font-bold mb-4">Constructure Project Brain</h1>
      <div className="w-full max-w-2xl flex flex-col gap-2 border border-gray-700 rounded p-3 bg-neutral-900">
        <div className="flex-1 max-h-96 overflow-y-auto space-y-2">
          {messages.map((m, i) => {
            if (m.role === "user") {
              return (
                <div key={i} className="text-right">
                  <span className="inline-block px-2 py-1 rounded bg-blue-500 text-white whitespace-pre-wrap">
                    <strong>You: </strong>
                    {m.content}
                  </span>
                </div>
              );
            }

            if (m.type === "structured") {
              const msg = m as Extract<Message, { type: "structured" }>;
              return (
                <div key={i} className="text-left space-y-1">
                  <span className="inline-block px-2 py-1 rounded bg-gray-200 text-black whitespace-pre-wrap">
                    <strong>AI: </strong>
                    {msg.content}
                  </span>
                  <div className="overflow-x-auto">
                    <table className="text-xs border mt-1 bg-white text-black">
                      <thead>
                        <tr>
                          <th className="border px-1">Mark</th>
                          <th className="border px-1">Location</th>
                          <th className="border px-1">Width (mm)</th>
                          <th className="border px-1">Height (mm)</th>
                          <th className="border px-1">Fire rating</th>
                          <th className="border px-1">Material</th>
                        </tr>
                      </thead>
                      <tbody>
                        {msg.data.map((d, idx) => (
                          <tr key={idx}>
                            <td className="border px-1">{d.mark}</td>
                            <td className="border px-1">{d.location}</td>
                            <td className="border px-1">{d.width_mm}</td>
                            <td className="border px-1">{d.height_mm}</td>
                            <td className="border px-1">{d.fire_rating}</td>
                            <td className="border px-1">{d.material}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              );
            }

            const msg = m as Extract<Message, { type: "qa" }>;
            return (
              <div key={i} className="text-left">
                <span className="inline-block px-2 py-1 rounded bg-gray-200 text-black whitespace-pre-wrap">
                  <strong>AI: </strong>
                  {msg.content}
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="mt-1 text-xs text-gray-700">
                      Sources:{" "}
                      {msg.sources.map((s, j) => (
                        <span key={j}>
                          {s.file_name} p.{s.page}
                          {j < msg.sources.length - 1 && ", "}
                        </span>
                      ))}
                    </div>
                  )}
                </span>
              </div>
            );
          })}
          {loading && <div>AI is thinking…</div>}
        </div>
        <div className="flex gap-2">
          <input
            className="flex-1 border border-gray-700 rounded px-2 py-1 bg-black text-white"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !loading && sendMessage()}
            placeholder="Ask about the project… or type 'Generate a door schedule'"
          />
          <button
            className="bg-white text-black px-4 py-1 rounded"
            onClick={sendMessage}
            disabled={loading}
          >
            Send
          </button>
        </div>
      </div>
    </main>
  );
}
