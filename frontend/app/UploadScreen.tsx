import { ChangeEventHandler } from "react";

type UploadScreenProps = {
  isUploading: boolean;
  uploadError: string;
  onUpload: ChangeEventHandler<HTMLInputElement>;
};

export default function UploadScreen({
  isUploading,
  uploadError,
  onUpload,
}: UploadScreenProps) {
  return (
    <main className="studybuddy-upload-screen">
      <div className="studybuddy-upload-hero">
        <div className="studybuddy-empty-badge">StudyBuddy</div>
        <h1>
          Transform notes into <span>intelligence.</span>
        </h1>
        <p>
          Learn faster. Upload your study materials to chat, and generate quizzes, flashcards, and summaries.
        </p>
      </div>

      <section className="studybuddy-upload-card">
        <label className="studybuddy-upload-dropzone studybuddy-upload-dropzone-large">
          <span className="studybuddy-upload-icon">↑</span>
          <h2>Upload Document</h2>
          <span className="studybuddy-upload-copy">
            {isUploading
              ? "Uploading and preparing your document..."
              : "Drop your PDF, DOCX or TXT files here to start."}
          </span>
          <span className="studybuddy-upload-button">Browse Files</span>
          <input className="hidden" onChange={onUpload} type="file" />
        </label>

        <div className="studybuddy-upload-meta">
          PDF &nbsp; · &nbsp; DOCX &nbsp; · &nbsp; TXT
        </div>
        {uploadError ? (
          <p className="studybuddy-upload-error">{uploadError}</p>
        ) : null}
      </section>

      <p className="studybuddy-upload-footnote">
        Simple, secure, and focused learning.
      </p>
    </main>
  );
}
