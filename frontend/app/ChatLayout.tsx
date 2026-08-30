import { Show, UserButton } from "@clerk/nextjs";
import { ChangeEventHandler, ReactNode } from "react";

import ActionButtons from "./ActionButtons";
import { ChatMode, UploadResponse } from "./types";

type ChatLayoutProps = {
  children: ReactNode;
  footer: ReactNode;
  uploads: UploadResponse[];
  uploadError: string;
  isUploading: boolean;
  isSending: boolean;
  onUpload: ChangeEventHandler<HTMLInputElement>;
  onAction: (mode: ChatMode) => void;
  activeSessionLabel: string;
};

export default function ChatLayout({
  children,
  footer,
  uploads,
  uploadError,
  isUploading,
  isSending,
  onUpload,
  onAction,
  activeSessionLabel,
}: ChatLayoutProps) {
  const hasUploads = uploads.length > 0;

  return (
    <main className="studybuddy-shell">
      <aside className="studybuddy-sidebar">
        <div>
          <div className="studybuddy-brand">
            <h1>StudyBuddy AI</h1>
            <p>Your personal study assistant</p>
            <p></p>
          </div>
        </div>

        <div className="space-y-6">
          <ActionButtons
            disabled={!hasUploads || isSending}
            onAction={onAction}
          />

          <section className="studybuddy-upload-panel">
            <p className="studybuddy-upload-title">Upload Document</p>
            <label className="studybuddy-upload-dropzone">
              <span className="studybuddy-upload-icon">↑</span>
              <span className="studybuddy-upload-copy">
                {isUploading ? "Uploading..." : "Drop your PDF, DOCX or TXT files here to start."}
              </span>
              <span className="studybuddy-upload-button">Browse Files</span>
              <input className="hidden" onChange={onUpload} type="file" />
            </label>
            <div className="studybuddy-upload-meta">
              {uploads.length > 0 ? `${uploads.length} document(s) uploaded` : "PDF · DOCX · TXT"}
            </div>
            {uploadError ? (
              <p className="studybuddy-upload-error">{uploadError}</p>
            ) : null}
            {hasUploads ? (
              <div className="mt-4 space-y-2">
                {uploads.map((upload) => (
                  <div
                    key={upload.document_id}
                    className="rounded-2xl border border-slate-200/70 bg-slate-50 px-3 py-2 text-sm text-[#a1a7bc]"
                  >
                    {upload.document_name}
                  </div>
                ))}
              </div>
            ) : null}
          </section>

        </div>
      </aside>

      <section className="studybuddy-main">
        <header className="studybuddy-topbar">
          <div className="studybuddy-session-pill">
            <span className="studybuddy-session-dot" />
            <span>Active Session: {activeSessionLabel}</span>
          </div>
          <div className="studybuddy-auth-shell">
            <Show when="signed-in">
              <div className="studybuddy-auth-user">
                <span>My Account</span>
                <UserButton afterSignOutUrl="/" />
              </div>
            </Show>
          </div>
        </header>

        <div className="studybuddy-chat-stage">{children}</div>
        {footer}
      </section>
    </main>
  );
}
