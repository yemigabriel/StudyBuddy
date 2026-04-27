"use client";

import { useMemo, useState } from "react";

type QuizQuestion = {
  question: string;
  options: string[];
  answer: string;
};

type QuizData = {
  questions: QuizQuestion[];
};

type QuizModalProps = {
  quizData: QuizData;
  onClose: () => void;
};

export default function QuizModal({ quizData, onClose }: QuizModalProps) {
  const [selectedAnswers, setSelectedAnswers] = useState<Record<number, string>>({});
  const [score, setScore] = useState<number | null>(null);
  const [showResults, setShowResults] = useState(false);

  const totalQuestions = quizData.questions.length;
  const correctAnswers = useMemo(
    () =>
      quizData.questions.reduce((count, question, index) => {
        return count + (selectedAnswers[index] === question.answer ? 1 : 0);
      }, 0),
    [quizData.questions, selectedAnswers],
  );

  function handleSubmit() {
    setScore(correctAnswers);
    setShowResults(true);
  }

  function handleRetry() {
    setSelectedAnswers({});
    setScore(null);
    setShowResults(false);
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 px-4">
      <div className="max-h-[85vh] w-full max-w-3xl overflow-y-auto rounded-xl bg-white p-6 shadow-xl">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h3 className="text-2xl font-semibold text-slate-900">Generated Quiz</h3>
            <p className="mt-1 text-sm text-slate-600">
              Answer the questions below and submit when you are ready.
            </p>
          </div>
          <button
            className="rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50"
            onClick={onClose}
            type="button"
          >
            Close
          </button>
        </div>

        <div className="mt-6 space-y-6">
          {quizData.questions.map((question, questionIndex) => (
            <div
              key={`${question.question}-${questionIndex}`}
              className="rounded-lg border border-slate-200 p-4"
            >
              <p className="font-medium text-slate-900">
                {questionIndex + 1}. {question.question}
              </p>
              <div className="mt-4 space-y-2">
                {question.options.map((option) => {
                  const isSelected = selectedAnswers[questionIndex] === option;
                  const isCorrect = option === question.answer;
                  const isWrongSelection = showResults && isSelected && !isCorrect;
                  const isCorrectHighlight = showResults && isCorrect;

                  return (
                    <label
                      key={`${questionIndex}-${option}`}
                      className={`flex cursor-pointer items-center gap-3 rounded-md border px-3 py-2 text-sm ${
                        isCorrectHighlight
                          ? "border-emerald-300 bg-emerald-50 text-emerald-800"
                          : isWrongSelection
                            ? "border-rose-300 bg-rose-50 text-rose-800"
                            : "border-slate-200 text-slate-700 hover:bg-slate-50"
                      }`}
                    >
                      <input
                        checked={isSelected}
                        className="h-4 w-4"
                        disabled={showResults}
                        name={`question-${questionIndex}`}
                        onChange={() =>
                          setSelectedAnswers((current) => ({
                            ...current,
                            [questionIndex]: option,
                          }))
                        }
                        type="radio"
                        value={option}
                      />
                      <span>{option}</span>
                    </label>
                  );
                })}
              </div>
            </div>
          ))}
        </div>

        <div className="mt-6 flex flex-wrap items-center gap-3">
          <button
            className="rounded-md bg-slate-900 px-5 py-3 text-white disabled:opacity-60"
            disabled={showResults || totalQuestions === 0}
            onClick={handleSubmit}
            type="button"
          >
            Submit Quiz
          </button>
          {showResults ? (
            <button
              className="rounded-md border border-slate-300 px-5 py-3 text-slate-700 hover:bg-slate-50"
              onClick={handleRetry}
              type="button"
            >
              Retry
            </button>
          ) : null}
          {score !== null ? (
            <p className="text-sm font-medium text-slate-700">
              Score: {score}/{totalQuestions}
            </p>
          ) : null}
        </div>
      </div>
    </div>
  );
}
