export type QType = "Y1" | "Y2" | "O1" | "O2";

export interface VariantBrief {
  id: number;
  title: string;
  status: "draft" | "ready";
  created_at: string | null;
  question_count: number;
}

export interface Progress {
  by_type: Record<QType, number>;
  filled: number;
  total_slots: number;
  needs_image: number;
  percent: number;
}

export interface QuestionImage {
  id: number;
  url: string;
  caption: string | null;
}

export interface Y1Option {
  id?: number;
  text: string;
  is_correct: boolean;
}

export interface Y2Pair {
  id?: number;
  left: string;   // текст подвопроса
  right: string;  // правильный ответ — буква A-F
}

export interface Y2Option {
  id?: number;
  text: string;   // текст варианта ответа (для буквы A-F)
}

export interface O1Answer {
  id?: number;
  text: string;
  match_mode: "exact" | "numeric";
  tolerance: number | null;
}

export interface O2Band {
  id?: number;
  band_no: number;
  prompt: string | null;
  reference_answer: string;
  match_mode: "exact" | "numeric";
  tolerance: number | null;
  max_points: number;
}

export interface CertQuestion {
  id: number;
  number: number;
  part: 1 | 2;
  qtype: QType;
  text: string;
  points: number;
  needs_image: boolean;
  images: QuestionImage[];
  options?: Y1Option[];  // Y1: варианты ответа
  y2options?: Y2Option[];  // Y2: варианты A-F
  pairs?: Y2Pair[];  // Y2: подвопросы с правильными ответами
  answers?: O1Answer[];
  bands?: O2Band[];
}

export interface Variant {
  id: number;
  title: string;
  status: "draft" | "ready";
  part1_timer_sec: number;
  part2_timer_sec: number;
  created_at: string | null;
  questions: CertQuestion[];
  progress: Progress;
}

export const SECTION_RANGES: Record<QType, [number, number]> = {
  Y1: [1, 32],
  Y2: [33, 35],
  O1: [36, 40],
  O2: [41, 43],
};

export const SECTION_LABELS: Record<QType, string> = {
  Y1: "Одна альтернатива",
  Y2: "Сопоставление",
  O1: "Краткий ответ",
  O2: "Письменная работа",
};

// ---------- Прохождение теста учеником ----------

export interface TakeOption { id: number; text: string }
export interface TakePairItem { id: number; text: string }
export interface TakeBand { id: number; band_no: number; prompt: string | null; max_points: number }
export interface TakeImage { id: number; url: string }

export interface TakeQuestion {
  id: number;
  number: number;
  part: 1 | 2;
  qtype: QType;
  text: string;
  points: number;
  images: TakeImage[];
  options?: TakeOption[];       // Y1: варианты ответа
  subquestions?: TakePairItem[]; // Y2: подвопросы (33-35)
  lefts?: TakePairItem[];        // Y2 legacy
  rights?: TakePairItem[];       // Y2 legacy
  bands?: TakeBand[];
  answered?: boolean;
  your_answer?: Record<string, unknown>;
  is_correct?: boolean | null;
  points_earned?: number;
}

export interface AttemptView {
  id: number;
  status: "part1" | "part2" | "finished";
  part1_seconds_left: number;
  part2_seconds_left: number | null;
  questions: TakeQuestion[];
}

export interface PartResult { earned: number; max: number; percent: number }
export interface ResultsView { part1: PartResult; part2: PartResult; total: PartResult; status: string }
