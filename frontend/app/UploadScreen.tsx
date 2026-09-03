import { Show, SignInButton, SignUpButton, UserButton } from "@clerk/nextjs";
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
      <div className="studybuddy-auth-bar">
        <Show when="signed-out">
          <div className="studybuddy-auth-actions">
            <SignInButton mode="modal">
              <button className="studybuddy-auth-button studybuddy-auth-button-secondary" type="button">
                Sign In
              </button>
            </SignInButton>
            <SignUpButton mode="modal">
              <button className="studybuddy-auth-button studybuddy-auth-button-primary" type="button">
                Sign Up
              </button>
            </SignUpButton>
          </div>
        </Show>
        <Show when="signed-in">
          <div className="studybuddy-auth-user">
            <span>Signed in</span>
            <UserButton />
          </div>
        </Show>
      </div>

      <div className="studybuddy-upload-intro">
        <p className="studybuddy-upload-kicker">StudyBuddy</p>
        <h1>Study from your own documents</h1>
        <p>
          Upload a PDF, DOCX, or TXT file to start a study session.
        </p>
      </div>

      <section className="studybuddy-upload-card">
        <label className="studybuddy-upload-dropzone studybuddy-upload-dropzone-large">
          <span className="studybuddy-upload-icon">↑</span>
          <span className="studybuddy-upload-copy">
            {isUploading
              ? "Uploading and preparing your document..."
              : "Drop your file here or browse to upload."}
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
    </main>
  );
}
