"use client";

import { FormEvent, useEffect, useState } from "react";

import QuizModal from "./QuizModal";

type ChatMode = "qa" | "summary" | "quiz";

type QuizQuestion = {
  question: string;
  options: string[];
  answer: string;
};

type QuizPayload = {
  questions: QuizQuestion[];
};

type ChatResponse = {
  response: string;
  session_id: string;
  context: string[];
  type: string;
  message?: string | null;
  options: string[];
  document_name?: string | null;
  mode: ChatMode;
  quiz?: QuizPayload | null;
};

type UploadResponse = {
  document_id: string;
  document_name: string;
  filename: string;
  content_type: string;
  size: number;
  chunks: number;
};

type Message = {
  role: "user" | "assistant";
  content: string;
};

type StreamEventPayload = {
  content?: string;
  response?: string;
  session_id?: string;
  context?: string[];
  message?: string | null;
  options?: string[];
  document_name?: string | null;
  mode?: ChatMode;
  questions?: QuizQuestion[];
};

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export default function Home() {
  const [sessionId, setSessionId] = useState("");
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [pendingQuery, setPendingQuery] = useState("");
  const [pendingMode, setPendingMode] = useState<ChatMode>("qa");
  const [disambiguation, setDisambiguation] = useState<ChatResponse | null>(null);
  const [uploads, setUploads] = useState<UploadResponse[]>([]);
  const [quizData, setQuizData] = useState<QuizPayload | null>(null);
  const [showQuizModal, setShowQuizModal] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  useEffect(() => {
    const savedSessionId = window.sessionStorage.getItem("studybuddy-session-id");
    if (savedSessionId) {
      setSessionId(savedSessionId);
      return;
    }

    const nextSessionId = crypto.randomUUID();
    window.sessionStorage.setItem("studybuddy-session-id", nextSessionId);
    setSessionId(nextSessionId);
  }, []);

  async function handleUpload(event: FormEvent<HTMLInputElement>) {
    const file = event.currentTarget.files?.[0];
    if (!file || !sessionId) {
      return;
    }

    setIsUploading(true);
    const formData = new FormData();
    formData.append("session_id", sessionId);
    formData.append("file", file);

    try {
      const response = await fetch(`${API_BASE_URL}/upload`, {
        method: "POST",
        body: formData,
      });
      const data: UploadResponse = await response.json();
      setUploads((current) => [...current, data]);
    } finally {
      setIsUploading(false);
      event.currentTarget.value = "";
    }
  }

  async function sendQuestion(
    message: string,
    mode: ChatMode = "qa",
    documentName?: string,
    appendUserMessage: boolean = true,
  ) {
    if (!message.trim() || !sessionId) {
      return;
    }

    setIsSending(true);
    setDisambiguation(null);
    if (appendUserMessage) {
      setMessages((current) => [...current, { role: "user", content: message }]);
    }

    try {
      const response = await fetch(`${API_BASE_URL}/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message,
          session_id: sessionId,
          document_name: documentName,
          mode,
        }),
      });
      if (!response.ok || !response.body) {
        throw new Error("Streaming request failed.");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let assistantIndex = -1;

      setMessages((current) => {
        assistantIndex = current.length;
        return [...current, { role: "assistant", content: "" }];
      });

      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const events = buffer.split("\n\n");
        buffer = events.pop() ?? "";

        for (const rawEvent of events) {
          const parsed = parseSseEvent(rawEvent);
          if (!parsed) {
            continue;
          }

          if (parsed.event === "disambiguation") {
            const payload = parsed.payload;
            setPendingQuery(message);
            setPendingMode(mode);
            setDisambiguation({
              response: "",
              session_id: payload.session_id ?? sessionId,
              context: [],
              type: "disambiguation",
              message: payload.message ?? "Which document are you referring to?",
              options: payload.options ?? [],
              document_name: payload.document_name ?? null,
              mode,
            });
            setMessages((current) => {
              const next = [...current];
              next[assistantIndex] = {
                role: "assistant",
                content: payload.message ?? "Which document are you referring to?",
              };
              return next;
            });
            return;
          }

          if (parsed.event === "quiz") {
            if (parsed.payload.questions?.length) {
              setQuizData({ questions: parsed.payload.questions });
              setShowQuizModal(true);
            }
          }

          if (parsed.event === "chunk") {
            const token = parsed.payload.content ?? "";
            setMessages((current) => {
              const next = [...current];
              next[assistantIndex] = {
                role: "assistant",
                content: `${next[assistantIndex]?.content ?? ""}${token}`,
              };
              return next;
            });
          }

          if (parsed.event === "done") {
            setPendingQuery("");
            if (mode === "summary" && parsed.payload.response) {
              setMessages((current) => {
                const next = [...current];
                next[assistantIndex] = {
                  role: "assistant",
                  content: parsed.payload.response ?? "",
                };
                return next;
              });
            }

            if (mode === "quiz") {
              setMessages((current) => {
                const next = [...current];
                next[assistantIndex] = {
                  role: "assistant",
                  content: parsed.payload.response ?? "Quiz generated successfully.",
                };
                return next;
              });
            }
          }
        }
      }
    } catch {
      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content: "I couldn't stream a response right now. Please try again.",
        },
      ]);
    } finally {
      setIsSending(false);
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const message = question.trim();
    if (!message) {
      return;
    }
    setQuestion("");
    await sendQuestion(message, "qa");
  }

  async function handleSummarize() {
    const message = question.trim() || "Summarize this document.";
    setQuestion("");
    await sendQuestion(message, "summary");
  }

  async function handleGenerateQuiz() {
    const message = question.trim() || "Generate a quiz for this document.";
    setQuestion("");
    await sendQuestion(message, "quiz");
  }

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-4xl flex-col gap-6 px-6 py-12">
      <section className="rounded-xl bg-white p-6 shadow-sm">
        <h1 className="text-3xl font-semibold">StudyBuddy</h1>
        <p className="mt-2 text-slate-600">
          Upload study material and chat with your notes.
        </p>
      </section>

      <section className="rounded-xl bg-white p-6 shadow-sm">
        <h2 className="text-xl font-medium">Upload</h2>
        <input
          className="mt-4 block w-full rounded-md border border-slate-300 p-3"
          type="file"
          onChange={handleUpload}
        />
        <p className="mt-3 text-sm text-slate-500">
          {isUploading ? "Uploading..." : `${uploads.length} document(s) uploaded in this session.`}
        </p>
        {uploads.length > 0 ? (
          <div className="mt-4 flex flex-wrap gap-2">
            {uploads.map((upload) => (
              <span
                key={upload.document_id}
                className="rounded-full bg-slate-100 px-3 py-1 text-sm text-slate-700"
              >
                {upload.document_name}
              </span>
            ))}
          </div>
        ) : null}
      </section>

      <section className="rounded-xl bg-white p-6 shadow-sm">
        <h2 className="text-xl font-medium">Chat</h2>
        <div className="mt-4 min-h-48 rounded-md border border-dashed border-slate-300 p-4">
          {messages.length === 0 ? (
            <p className="text-slate-500">Responses will appear here.</p>
          ) : (
            <div className="space-y-4">
              {messages.map((message, index) => (
                <div key={`${message.role}-${index}`}>
                  <p className="text-xs uppercase tracking-wide text-slate-400">
                    {message.role}
                  </p>
                  <p className="mt-1 whitespace-pre-wrap text-slate-700">
                    {message.content}
                  </p>
                </div>
              ))}
            </div>
          )}

          {disambiguation ? (
            <div className="mt-4 border-t border-slate-200 pt-4">
              <p className="text-sm font-medium text-slate-700">
                Pick a document:
              </p>
              <div className="mt-3 flex flex-wrap gap-2">
                {disambiguation.options.map((option) => (
                  <button
                    key={option}
                    className="rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50"
                    onClick={() => void sendQuestion(pendingQuery, pendingMode, option, false)}
                    type="button"
                  >
                    {option}
                  </button>
                ))}
              </div>
            </div>
          ) : null}
        </div>

        <form className="mt-4 flex gap-3" onSubmit={handleSubmit}>
          <input
            className="flex-1 rounded-md border border-slate-300 p-3"
            placeholder="Ask a question about your material..."
            type="text"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
          />
          <button
            className="rounded-md bg-slate-900 px-5 py-3 text-white disabled:opacity-60"
            disabled={isSending || !sessionId}
            type="submit"
          >
            {isSending ? "Sending..." : "Send"}
          </button>
        </form>
        <div className="mt-3 flex flex-wrap gap-3">
          <button
            className="rounded-md border border-slate-300 px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 disabled:opacity-60"
            disabled={isSending || !sessionId}
            onClick={() => void handleSummarize()}
            type="button"
          >
            Summarize Document
          </button>
          <button
            className="rounded-md border border-slate-300 px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 disabled:opacity-60"
            disabled={isSending || !sessionId}
            onClick={() => void handleGenerateQuiz()}
            type="button"
          >
            Generate Quiz
          </button>
        </div>
      </section>
      {showQuizModal && quizData ? (
        <QuizModal
          onClose={() => setShowQuizModal(false)}
          quizData={quizData}
        />
      ) : null}
    </main>
  );
}

function parseSseEvent(rawEvent: string): { event: string; payload: StreamEventPayload } | null {
  const lines = rawEvent.split("\n");
  const eventLine = lines.find((line) => line.startsWith("event: "));
  const dataLine = lines.find((line) => line.startsWith("data: "));
  if (!eventLine || !dataLine) {
    return null;
  }

  try {
    return {
      event: eventLine.slice(7).trim(),
      payload: JSON.parse(dataLine.slice(6)),
    };
  } catch {
    return null;
  }
}
