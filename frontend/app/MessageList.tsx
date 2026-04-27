import { ChatResponse, Message } from "./types";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

type MessageListProps = {
  messages: Message[];
  disambiguation: ChatResponse | null;
  pendingQuery: string;
  onDisambiguate: (documentName: string) => void;
};

export default function MessageList({
  messages,
  disambiguation,
  pendingQuery,
  onDisambiguate,
}: MessageListProps) {
  if (messages.length === 0) {
    return (
      <div className="studybuddy-empty-state">
        <div className="studybuddy-empty-badge">Ready to study</div>
        <h2>Ask anything about your uploaded material.</h2>
        <p>
          Use the action buttons to summarize, generate a quiz, make flashcards,
          or ask a direct question from your document.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {messages.map((message, index) => (
        <div
          key={`${message.role}-${index}-${pendingQuery}`}
          className={`studybuddy-message-row ${message.role === "assistant" ? "justify-start" : "justify-end"}`}
        >
          {message.role === "assistant" ? (
            <div className="studybuddy-message-icon">✦</div>
          ) : null}
          <div
            className={`studybuddy-message-bubble ${
              message.role === "assistant"
                ? "studybuddy-message-assistant"
                : "studybuddy-message-user"
            }`}
          >
            {message.role === "assistant" && !message.content ? (
              <div className="studybuddy-loading-dots" aria-label="Loading response">
                <span />
                <span />
                <span />
              </div>
            ) : message.role === "assistant" ? (
              <div className="studybuddy-markdown">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {message.content}
                </ReactMarkdown>
              </div>
            ) : (
              <p className="whitespace-pre-wrap">{message.content}</p>
            )}

            {disambiguation && index === messages.length - 1 ? (
              <div className="mt-5 flex flex-wrap gap-2">
                {disambiguation.options.map((option) => (
                  <button
                    key={option}
                    className="studybuddy-chip"
                    onClick={() => onDisambiguate(option)}
                    type="button"
                  >
                    {option}
                  </button>
                ))}
              </div>
            ) : null}
          </div>
          {message.role === "user" ? (
            <div className="studybuddy-message-icon studybuddy-user-icon">◔</div>
          ) : null}
        </div>
      ))}
    </div>
  );
}
