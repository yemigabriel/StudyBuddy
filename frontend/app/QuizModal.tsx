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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/45 px-4">
      <div className="w-full max-w-3xl rounded-[28px] bg-white p-6 shadow-[0_30px_80px_rgba(58,61,149,0.22)]">
        <div className="flex items-center justify-between gap-4">
          <div className="text-xs font-semibold uppercase tracking-[0.22em] text-[#7d7ef7]">
            Question {currentIndex + 1} of {totalQuestions}
          </div>
          <button
            aria-label="Close quiz"
            className="inline-flex items-center gap-2 rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-600 transition hover:bg-slate-100 hover:text-slate-900"
            onClick={onClose}
            type="button"
          >
            <span aria-hidden="true">✕</span>
            <span>Close</span>
          </button>
        </div>

        <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-slate-200">
          <div
            className="h-full rounded-full bg-[#4b4cf3]"
            style={{ width: `${((currentIndex + 1) / totalQuestions) * 100}%` }}
          />
        </div>

        <div className="mt-12">
          <h3 className="max-w-2xl text-2xl font-semibold leading-snug text-slate-900">
            {question.question}
          </h3>
          <div className="mt-4 h-1 w-16 rounded-full bg-[#4b4cf3]" />
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
                    ? "border-[#4b4cf3] bg-[#eef0ff]"
                    : isWrongSelection
                      ? "border-rose-300 bg-rose-50"
                      : isSelected
                        ? "border-[#4b4cf3] bg-white shadow-[0_12px_22px_rgba(75,76,243,0.12)]"
                        : "border-slate-200 bg-slate-50/70 hover:bg-white"
                }`}
              >
                <span
                  className={`inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-sm font-semibold ${
                    isSelected || isCorrectHighlight
                      ? "bg-[#4b4cf3] text-white"
                      : "bg-white text-slate-500"
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
                <span className="text-sm font-medium text-slate-700">{option}</span>
                {isSelected ? (
                  <span className="ml-auto text-[#4b4cf3]">●</span>
                ) : null}
              </label>
            );
          })}
        </div>

        <div className="mt-10 flex items-center justify-between gap-3">
          <button
            className="rounded-full px-4 py-3 text-sm font-medium text-slate-500 transition hover:bg-slate-50 disabled:opacity-40"
            disabled={currentIndex === 0}
            onClick={handlePrevious}
            type="button"
          >
            ← Previous
          </button>

          <div className="flex items-center gap-3">
            {showResults ? (
              <p className="text-sm font-semibold text-slate-700">
                Score: {score}/{totalQuestions}
              </p>
            ) : null}
            {showResults ? (
              <button
                className="rounded-full border border-slate-200 px-5 py-3 text-sm font-medium text-slate-600 transition hover:bg-slate-50"
                onClick={handleRetry}
                type="button"
              >
                Retry
              </button>
            ) : (
              <button
                className="rounded-full border border-slate-200 px-5 py-3 text-sm font-medium text-slate-500 transition hover:bg-slate-50"
                onClick={() => setShowResults(true)}
                type="button"
              >
                Submit Quiz
              </button>
            )}
            <button
              className="rounded-full border border-slate-200 px-5 py-3 text-sm font-medium text-slate-600 transition hover:bg-slate-50"
              onClick={onClose}
              type="button"
            >
              Exit Quiz
            </button>
            <button
              className="rounded-full bg-[#4b4cf3] px-6 py-3 text-sm font-semibold text-white shadow-[0_14px_26px_rgba(75,76,243,0.28)] disabled:opacity-40"
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
