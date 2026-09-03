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
    <div className="fixed inset-0 z-50 overflow-y-auto bg-black/20 px-4 py-6">
      <div className="mx-auto flex min-h-full w-full max-w-2xl items-center justify-center">
        <div className="studybuddy-modal-panel w-full max-w-2xl overflow-y-auto rounded-[24px] border border-black/10 bg-white p-6 shadow-[0_18px_40px_rgba(0,0,0,0.10)]">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 text-sm font-semibold text-neutral-700">
            <span className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-black/[0.05] text-black">
              ◫
            </span>
            <span>Study Flashcards</span>
          </div>
          <button
            aria-label="Close flashcards"
            className="inline-flex items-center gap-2 rounded-full border border-black/10 px-4 py-2 text-sm font-semibold text-neutral-600 transition hover:bg-black/[0.04] hover:text-black"
            onClick={onClose}
            type="button"
          >
            <span aria-hidden="true">✕</span>
            <span>Close</span>
          </button>
        </div>

        <div className="mt-5 flex items-center gap-4">
          <div className="h-2 flex-1 overflow-hidden rounded-full bg-black/[0.06]">
            <div
              className="h-full rounded-full bg-black transition-all"
              style={{ width: `${((currentIndex + 1) / totalCards) * 100}%` }}
            />
          </div>
          <span className="text-xs font-semibold uppercase tracking-[0.22em] text-neutral-400">
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
            className="rounded-full bg-black px-8 py-3 text-sm font-semibold text-white shadow-[0_10px_20px_rgba(0,0,0,0.12)]"
            onClick={() => setFlipped((current) => !current)}
            type="button"
          >
            {flipped ? "Show Front" : "Flip Card"}
          </button>
        </div>

        <div className="mt-8 flex items-center justify-between">
          <button
            className="rounded-full border border-black/10 px-5 py-3 text-sm font-medium text-neutral-600 transition hover:bg-black/[0.04] disabled:opacity-40"
            disabled={currentIndex === 0}
            onClick={goToPrevious}
            type="button"
          >
            Previous
          </button>
          <div className="flex items-center gap-3">
            <button
              className="rounded-full border border-black/10 px-5 py-3 text-sm font-medium text-neutral-600 transition hover:bg-black/[0.04]"
              onClick={onClose}
              type="button"
            >
              Exit Flashcards
            </button>
            <button
              className="rounded-full bg-black px-5 py-3 text-sm font-semibold text-white transition disabled:opacity-40"
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
    </div>
  );
}
