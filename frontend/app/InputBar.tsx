import { FormEvent } from "react";

type InputBarProps = {
  value: string;
  disabled: boolean;
  onChange: (value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
};

export default function InputBar({
  value,
  disabled,
  onChange,
  onSubmit,
}: InputBarProps) {
  return (
    <footer className="studybuddy-input-shell">
      <form className="studybuddy-input-card" onSubmit={onSubmit}>
        <div className="studybuddy-input-row">
          <input
            className="studybuddy-input"
            disabled={disabled}
            onChange={(event) => onChange(event.target.value)}
            placeholder="Ask anything about your study material..."
            type="text"
            value={value}
          />
          <button
            className="studybuddy-send-button"
            disabled={disabled}
            type="submit"
          >
            ↑
          </button>
        </div>
      </form>
    </footer>
  );
}
