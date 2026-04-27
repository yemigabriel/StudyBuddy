import { ChatMode } from "./types";

type ActionButtonsProps = {
  disabled: boolean;
  onAction: (mode: ChatMode) => void;
};

const ACTIONS: Array<{ mode: ChatMode; label: string; variant: "primary" | "secondary" }> = [
  { mode: "summary", label: "Summarize Document", variant: "primary" },
  { mode: "quiz", label: "Generate Quiz", variant: "secondary" },
  { mode: "flashcards", label: "Generate Flashcards", variant: "secondary" },
];

export default function ActionButtons({ disabled, onAction }: ActionButtonsProps) {
  return (
    <div className="space-y-3">
      {ACTIONS.map((action) => (
        <button
          key={action.mode}
          className={`studybuddy-action ${action.variant === "primary" ? "studybuddy-action-primary" : "studybuddy-action-secondary"}`}
          disabled={disabled}
          onClick={() => onAction(action.mode)}
          type="button"
        >
          <span className="studybuddy-action-icon" aria-hidden="true">
            {action.mode === "summary" ? "▣" : action.mode === "quiz" ? "?" : "◫"}
          </span>
          <span>{action.label}</span>
        </button>
      ))}
    </div>
  );
}
