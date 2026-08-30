export type ChatMode = "qa" | "summary" | "quiz" | "flashcards";

export type QuizQuestion = {
  question: string;
  options: string[];
  answer: string;
};

export type QuizPayload = {
  questions: QuizQuestion[];
};

export type Flashcard = {
  front: string;
  back: string;
};

export type FlashcardsPayload = {
  cards: Flashcard[];
};

export type ChatResponse = {
  response: string;
  session_id: string;
  context: string[];
  type: string;
  message?: string | null;
  options: string[];
  document_name?: string | null;
  mode: ChatMode;
  quiz?: QuizPayload | null;
  flashcards?: FlashcardsPayload | null;
};

export type UploadResponse = {
  document_id: string;
  document_name: string;
  filename: string;
  content_type: string;
  size: number;
  parsed_chunks: number;
  chunks: number;
  indexing_status: string;
  error?: string | null;
  detail?: string | null;
};

export type Message = {
  role: "user" | "assistant";
  content: string;
  timestamp?: string;
};

export type MemoryDocument = {
  document_id?: string | null;
  document_name: string;
};

export type MemoryPreviewResponse = {
  session_id: string;
  selected_document?: string | null;
  documents: MemoryDocument[];
  messages: Message[];
};

export type StreamEventPayload = {
  content?: string;
  response?: string;
  session_id?: string;
  context?: string[];
  message?: string | null;
  options?: string[];
  document_name?: string | null;
  mode?: ChatMode;
  questions?: QuizQuestion[];
  cards?: Flashcard[];
};
