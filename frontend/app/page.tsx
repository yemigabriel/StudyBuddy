"use client";

import { useAuth } from "@clerk/nextjs";
import { ChangeEvent, FormEvent, useEffect, useState } from "react";

import ChatLayout from "./ChatLayout";
import FlashcardsModal from "./FlashcardsModal";
import InputBar from "./InputBar";
import MessageList from "./MessageList";
import QuizModal from "./QuizModal";
import UploadScreen from "./UploadScreen";
import {
  ChatMode,
  ChatResponse,
  FlashcardsPayload,
  Message,
  QuizPayload,
  StreamEventPayload,
  UploadResponse,
} from "./types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

function createSessionId() {
  if (
    typeof globalThis.crypto !== "undefined" &&
    typeof globalThis.crypto.randomUUID === "function"
  ) {
    return globalThis.crypto.randomUUID();
  }

  return `session-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

function ensureBrowserSessionId(currentSessionId: string) {
  if (currentSessionId) {
    return currentSessionId;
  }

  const storedSessionId = window.sessionStorage.getItem("studybuddy-session-id");
  if (storedSessionId) {
    return storedSessionId;
  }

  const nextSessionId = createSessionId();
  window.sessionStorage.setItem("studybuddy-session-id", nextSessionId);
  return nextSessionId;
}

export default function Home() {
  const { isSignedIn } = useAuth();
  const [sessionId, setSessionId] = useState("");
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [pendingQuery, setPendingQuery] = useState("");
  const [pendingMode, setPendingMode] = useState<ChatMode>("qa");
  const [disambiguation, setDisambiguation] = useState<ChatResponse | null>(null);
  const [uploads, setUploads] = useState<UploadResponse[]>([]);
  const [quizData, setQuizData] = useState<QuizPayload | null>(null);
  const [flashcardsData, setFlashcardsData] = useState<FlashcardsPayload | null>(null);
  const [showQuizModal, setShowQuizModal] = useState(false);
  const [showFlashcardsModal, setShowFlashcardsModal] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const [hasActiveDocument, setHasActiveDocument] = useState(false);

  useEffect(() => {
    const savedSessionId = window.sessionStorage.getItem("studybuddy-session-id");
    if (savedSessionId) {
      setSessionId(savedSessionId);
      return;
    }

    const nextSessionId = createSessionId();
    window.sessionStorage.setItem("studybuddy-session-id", nextSessionId);
    setSessionId(nextSessionId);
  }, []);

  useEffect(() => {
    if (isSignedIn !== false) {
      return;
    }

    window.sessionStorage.removeItem("studybuddy-session-id");
    setSessionId("");
    setQuestion("");
    setMessages([]);
    setPendingQuery("");
    setPendingMode("qa");
    setDisambiguation(null);
    setUploads([]);
    setQuizData(null);
    setFlashcardsData(null);
    setShowQuizModal(false);
    setShowFlashcardsModal(false);
    setIsSending(false);
    setIsUploading(false);
    setUploadError("");
    setHasActiveDocument(false);
  }, [isSignedIn]);

  async function handleUpload(event: ChangeEvent<HTMLInputElement>) {
    const input = event.currentTarget;
    const file = input.files?.[0];
    if (!file) {
      return;
    }

    const effectiveSessionId = ensureBrowserSessionId(sessionId);
    if (!sessionId) {
      setSessionId(effectiveSessionId);
    }

    setIsUploading(true);
    setUploadError("");
    const formData = new FormData();
    formData.append("session_id", effectiveSessionId);
    formData.append("file", file);

    try {
      const response = await fetch(`${API_BASE_URL}/upload`, {
        method: "POST",
        body: formData,
      });
      const rawBody = await response.text();
      const data = rawBody ? (JSON.parse(rawBody) as UploadResponse) : null;

      if (!response.ok || !data) {
        throw new Error(
          data?.error ||
            `Upload failed with status ${response.status}.`,
        );
      }

      if (data.indexing_status === "indexed") {
        setUploads((current) => [...current, data]);
        setHasActiveDocument(true);
      } else {
        setUploadError(data.error ?? "Upload succeeded, but ingestion failed.");
      }
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "I couldn't upload the document right now. Please try again.";
      setUploadError(message);
    } finally {
      setIsUploading(false);
      if (input) {
        input.value = "";
      }
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

          if (parsed.event === "quiz" && parsed.payload.questions?.length) {
            setQuizData({ questions: parsed.payload.questions });
            setShowQuizModal(true);
          }

          if (parsed.event === "flashcards" && parsed.payload.cards?.length) {
            setFlashcardsData({ cards: parsed.payload.cards });
            setShowFlashcardsModal(true);
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
            if (mode !== "qa") {
              setMessages((current) => {
                const next = [...current];
                next[assistantIndex] = {
                  role: "assistant",
                  content:
                    parsed.payload.response ??
                    (mode === "summary"
                      ? "Summary generated successfully."
                      : mode === "quiz"
                        ? "Quiz generated successfully."
                        : "Flashcards generated successfully."),
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

  async function handleAction(mode: ChatMode) {
    const fallbackMessage =
      mode === "summary"
        ? "Summarize this document."
        : mode === "quiz"
          ? "Generate a quiz for this document."
          : "Generate flashcards for this document.";
    const message = question.trim() || fallbackMessage;
    setQuestion("");
    await sendQuestion(message, mode);
  }

  const activeSessionLabel = uploads[uploads.length - 1]?.document_name ?? "Study Session";

  return (
    <>
      {isUploading ? (
        <div className="studybuddy-upload-overlay" aria-live="polite" aria-busy="true">
          <div className="studybuddy-upload-overlay-card">
            <div className="studybuddy-upload-overlay-line" />
            <p className="studybuddy-upload-overlay-eyebrow">Upload in progress</p>
            <h2>Preparing your document...</h2>
            <p>
              StudyBuddy is preparing it for chat,
              summaries, quizzes, and flashcards.
            </p>
          </div>
        </div>
      ) : null}

      {!hasActiveDocument ? (
        <UploadScreen
          isUploading={isUploading}
          onUpload={handleUpload}
          uploadError={uploadError}
        />
      ) : (
      <ChatLayout
        activeSessionLabel={activeSessionLabel}
        footer={(
          <InputBar
            disabled={isSending || !sessionId}
            onChange={setQuestion}
            onSubmit={handleSubmit}
            value={question}
          />
        )}
        isSending={isSending}
        isUploading={isUploading}
        onAction={(mode) => void handleAction(mode)}
        onUpload={handleUpload}
        uploads={uploads}
      >
        <MessageList
          disambiguation={disambiguation}
          messages={messages}
          onDisambiguate={(documentName) =>
            void sendQuestion(pendingQuery, pendingMode, documentName, false)
          }
          pendingQuery={pendingQuery}
        />
      </ChatLayout>
      )}

      {showQuizModal && quizData ? (
        <QuizModal
          onClose={() => setShowQuizModal(false)}
          quizData={quizData}
        />
      ) : null}

      {showFlashcardsModal && flashcardsData ? (
        <FlashcardsModal
          flashcards={flashcardsData}
          onClose={() => setShowFlashcardsModal(false)}
        />
      ) : null}
    </>
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
