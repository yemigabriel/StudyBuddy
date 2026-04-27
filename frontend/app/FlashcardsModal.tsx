"use client";

import { useState } from "react";

import { FlashcardsPayload } from "./types";

type FlashcardsModalProps = {
  flashcards: FlashcardsPayload;
  onClose: () => void;
};

export default function FlashcardsModal({
  flashcards,
  onClose,
}: FlashcardsModalProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [flipped, setFlipped] = useState(false);

  const totalCards = flashcards.cards.length;
  const card = flashcards.cards[currentIndex];

  function goToNext() {
    setCurrentIndex((current) => Math.min(current + 1, totalCards - 1));
    setFlipped(false);
  }

  function goToPrevious() {
    setCurrentIndex((current) => Math.max(current - 1, 0));
    setFlipped(false);
  }

  if (!card) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-950/45 px-4 py-6">
      <div className="mx-auto flex min-h-full w-full max-w-2xl items-center justify-center">
        <div className="w-full max-w-2xl overflow-y-auto rounded-[32px] bg-white p-6 shadow-[0_28px_70px_rgba(54,59,123,0.25)] studybuddy-modal-panel">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 text-sm font-semibold text-slate-700">
            <span className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-[#eef0ff] text-[#4c4cf0]">
              ◫
            </span>
            <span>Study Flashcards</span>
          </div>
          <button
            className="rounded-full p-2 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700"
            onClick={onClose}
            type="button"
          >
            ✕
          </button>
        </div>

        <div className="mt-5 flex items-center gap-4">
          <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-100">
            <div
              className="h-full rounded-full bg-[#4b4cf3] transition-all"
              style={{ width: `${((currentIndex + 1) / totalCards) * 100}%` }}
            />
          </div>
          <span className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">
            {currentIndex + 1} / {totalCards}
          </span>
        </div>

        <button
          className={`studybuddy-flashcard mt-8 ${flipped ? "studybuddy-flashcard-flipped" : ""}`}
          onClick={() => setFlipped((current) => !current)}
          type="button"
        >
          <div className="studybuddy-flashcard-inner">
            <div className="studybuddy-flashcard-face">
              <p className="studybuddy-flashcard-label">
                {flipped ? "Answer" : "Concept Definition"}
              </p>
              <h3>{flipped ? card.back : card.front}</h3>
            </div>
          </div>
        </button>

        <div className="mt-6 flex justify-center">
          <button
            className="rounded-full bg-[#4b4cf3] px-8 py-3 text-sm font-semibold text-white shadow-[0_14px_28px_rgba(75,76,243,0.3)]"
            onClick={() => setFlipped((current) => !current)}
            type="button"
          >
            {flipped ? "Show Front" : "Flip Card"}
          </button>
        </div>

        <p className="mt-4 text-center text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">
          How well did you know this?
        </p>

        <div className="mt-5 grid gap-4 sm:grid-cols-2">
          <div className="rounded-2xl border border-rose-100 bg-rose-50 px-4 py-5 text-center text-sm font-semibold text-rose-500">
            Still learning
          </div>
          <div className="rounded-2xl border border-indigo-100 bg-indigo-50 px-4 py-5 text-center text-sm font-semibold text-[#4b4cf3]">
            I knew it
          </div>
        </div>

        <div className="mt-8 flex items-center justify-between">
          <button
            className="rounded-full border border-slate-200 px-5 py-3 text-sm font-medium text-slate-600 transition hover:bg-slate-50 disabled:opacity-40"
            disabled={currentIndex === 0}
            onClick={goToPrevious}
            type="button"
          >
            Previous
          </button>
          <button
            className="rounded-full bg-[#4b4cf3] px-5 py-3 text-sm font-semibold text-white transition disabled:opacity-40"
            disabled={currentIndex === totalCards - 1}
            onClick={goToNext}
            type="button"
          >
            Next
          </button>
        </div>
      </div>
      </div>
    </div>
  );
}
