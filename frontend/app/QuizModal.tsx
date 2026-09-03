"use client";

import { useMemo, useState } from "react";

import { QuizPayload } from "./types";

type QuizModalProps = {
  quizData: QuizPayload;
  onClose: () => void;
};

export default function QuizModal({ quizData, onClose }: QuizModalProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedAnswers, setSelectedAnswers] = useState<Record<number, string>>({});
  const [showResults, setShowResults] = useState(false);

  const totalQuestions = quizData.questions.length;
  const question = quizData.questions[currentIndex];
  const score = useMemo(
    () =>
      quizData.questions.reduce((count, item, index) => {
        return count + (selectedAnswers[index] === item.answer ? 1 : 0);
      }, 0),
    [quizData.questions, selectedAnswers],
  );

  function handleNext() {
    setCurrentIndex((current) => Math.min(current + 1, totalQuestions - 1));
  }

  function handlePrevious() {
    setCurrentIndex((current) => Math.max(current - 1, 0));
  }

  function handleRetry() {
    setCurrentIndex(0);
    setSelectedAnswers({});
    setShowResults(false);
  }

  if (!question) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/20 px-4">
      <div className="w-full max-w-3xl rounded-[24px] border border-black/10 bg-white p-6 shadow-[0_18px_40px_rgba(0,0,0,0.10)]">
        <div className="flex items-center justify-between gap-4">
          <div className="text-xs font-semibold uppercase tracking-[0.22em] text-neutral-500">
            Question {currentIndex + 1} of {totalQuestions}
          </div>
          <button
            aria-label="Close quiz"
            className="inline-flex items-center gap-2 rounded-full border border-black/10 px-4 py-2 text-sm font-semibold text-neutral-600 transition hover:bg-black/[0.04] hover:text-black"
            onClick={onClose}
            type="button"
          >
            <span aria-hidden="true">✕</span>
            <span>Close</span>
          </button>
        </div>

        <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-black/[0.08]">
          <div
            className="h-full rounded-full bg-black"
            style={{ width: `${((currentIndex + 1) / totalQuestions) * 100}%` }}
          />
        </div>

        <div className="mt-12">
          <h3 className="max-w-2xl text-2xl font-semibold leading-snug text-neutral-900">
            {question.question}
          </h3>
          <div className="mt-4 h-1 w-16 rounded-full bg-black" />
        </div>

        <div className="mt-10 space-y-4">
          {question.options.map((option, optionIndex) => {
            const key = String.fromCharCode(65 + optionIndex);
            const isSelected = selectedAnswers[currentIndex] === option;
            const isCorrect = option === question.answer;
            const isWrongSelection = showResults && isSelected && !isCorrect;
            const isCorrectHighlight = showResults && isCorrect;

            return (
              <label
                key={`${currentIndex}-${option}`}
                className={`flex cursor-pointer items-center gap-4 rounded-2xl border px-5 py-4 transition ${
                  isCorrectHighlight
                    ? "border-black bg-black/[0.04]"
                    : isWrongSelection
                      ? "border-neutral-300 bg-neutral-100"
                      : isSelected
                        ? "border-black bg-white shadow-[0_10px_20px_rgba(0,0,0,0.08)]"
                        : "border-black/10 bg-black/[0.02] hover:bg-white"
                }`}
              >
                <span
                  className={`inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-sm font-semibold ${
                    isSelected || isCorrectHighlight
                      ? "bg-black text-white"
                      : "bg-white text-neutral-500"
                  }`}
                >
                  {key}
                </span>
                <input
                  checked={isSelected}
                  className="hidden"
                  disabled={showResults}
                  name={`question-${currentIndex}`}
                  onChange={() =>
                    setSelectedAnswers((current) => ({
                      ...current,
                      [currentIndex]: option,
                    }))
                  }
                  type="radio"
                  value={option}
                />
                <span className="text-sm font-medium text-neutral-700">{option}</span>
                {isSelected ? (
                  <span className="ml-auto text-black">●</span>
                ) : null}
              </label>
            );
          })}
        </div>

        <div className="mt-10 flex items-center justify-between gap-3">
          <button
            className="rounded-full px-4 py-3 text-sm font-medium text-neutral-500 transition hover:bg-black/[0.04] disabled:opacity-40"
            disabled={currentIndex === 0}
            onClick={handlePrevious}
            type="button"
          >
            ← Previous
          </button>

          <div className="flex items-center gap-3">
            {showResults ? (
              <p className="text-sm font-semibold text-neutral-700">
                Score: {score}/{totalQuestions}
              </p>
            ) : null}
            {showResults ? (
              <button
                className="rounded-full border border-black/10 px-5 py-3 text-sm font-medium text-neutral-600 transition hover:bg-black/[0.04]"
                onClick={handleRetry}
                type="button"
              >
                Retry
              </button>
            ) : (
              <button
                className="rounded-full border border-black/10 px-5 py-3 text-sm font-medium text-neutral-500 transition hover:bg-black/[0.04]"
                onClick={() => setShowResults(true)}
                type="button"
              >
                Submit Quiz
              </button>
            )}
            <button
              className="rounded-full border border-black/10 px-5 py-3 text-sm font-medium text-neutral-600 transition hover:bg-black/[0.04]"
              onClick={onClose}
              type="button"
            >
              Exit Quiz
            </button>
            <button
              className="rounded-full bg-black px-6 py-3 text-sm font-semibold text-white shadow-[0_10px_18px_rgba(0,0,0,0.1)] disabled:opacity-40"
              disabled={currentIndex === totalQuestions - 1}
              onClick={handleNext}
              type="button"
            >
              Next Question →
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
