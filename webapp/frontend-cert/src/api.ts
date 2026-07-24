declare global {
  interface Window {
    Telegram?: { WebApp?: { initData: string; ready: () => void; expand: () => void } };
  }
}

function initData(): string {
  return window.Telegram?.WebApp?.initData ?? "";
}

async function request<T>(path: string, options: RequestInit = {}, planner = false): Promise<T> {
  const headers: Record<string, string> = {
    "X-Init-Data": initData(),
    ...(options.body && !(options.body instanceof FormData) ? { "Content-Type": "application/json" } : {}),
    ...(options.headers as Record<string, string> | undefined),
  };
  const basePrefix = planner ? "/api" : "/api/cert";
  const res = await fetch(`${basePrefix}${path}`, { ...options, headers });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.error || `Ошибка запроса (${res.status})`);
  }
  return data as T;
}

export const api = {
  listVariants: () => request<{ variants: import("./types").VariantBrief[] }>("/variants"),
  createVariant: (title: string) =>
    request<{ ok: boolean; id: number }>("/variants", { method: "POST", body: JSON.stringify({ title }) }),
  getVariant: (id: number) => request<import("./types").Variant>(`/variants/${id}`),
  deleteVariant: (id: number) => request<{ ok: boolean }>(`/variants/${id}`, { method: "DELETE" }),
  setStatus: (id: number, status: "draft" | "ready") =>
    request<{ ok: boolean }>(`/variants/${id}/status`, { method: "POST", body: JSON.stringify({ status }) }),

  importY1Text: (variantId: number, text: string) =>
    request<{ ok: boolean; added: number; found: number }>(`/variants/${variantId}/import-y1`, {
      method: "POST",
      body: JSON.stringify({ text }),
    }),
  importY1File: (variantId: number, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<{ ok: boolean; added: number; found: number }>(`/variants/${variantId}/import-y1`, {
      method: "POST",
      body: form,
    });
  },

  // v2: Markdown-aware import (preserves inline images and tables)
  importY1MdText: (variantId: number, text: string) =>
    request<{ ok: boolean; added: number; found: number }>(`/variants/${variantId}/import-y1-md`, {
      method: "POST",
      body: JSON.stringify({ text }),
    }),
  importY1MdFile: (variantId: number, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<{ ok: boolean; added: number; found: number }>(`/variants/${variantId}/import-y1-md`, {
      method: "POST",
      body: form,
    });
  },

  addQuestion: (variantId: number, payload: Record<string, unknown>) =>
    request<{ ok: boolean; question: import("./types").CertQuestion }>(`/variants/${variantId}/questions`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateQuestion: (questionId: number, payload: Record<string, unknown>) =>
    request<{ ok: boolean; question: import("./types").CertQuestion }>(`/questions/${questionId}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    }),
  deleteQuestion: (questionId: number) =>
    request<{ ok: boolean }>(`/questions/${questionId}`, { method: "DELETE" }),

  uploadImage: (questionId: number, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<{ ok: boolean; image: import("./types").QuestionImage }>(`/questions/${questionId}/images`, {
      method: "POST",
      body: form,
    });
  },
  deleteImage: (questionId: number, imageId: number) =>
    request<{ ok: boolean }>(`/questions/${questionId}/images/${imageId}`, { method: "DELETE" }),

  // ---------- прохождение теста ----------
  startAttempt: (variantId: number) =>
    request<{ ok: boolean; attempt_id: number }>("/attempts", { method: "POST", body: JSON.stringify({ variant_id: variantId }) }),
  getAttempt: (attemptId: number) => request<import("./types").AttemptView>(`/attempts/${attemptId}`),
  submitAnswer: (attemptId: number, questionId: number, payload: Record<string, unknown>) =>
    request<Record<string, unknown>>(`/attempts/${attemptId}/answer`, {
      method: "POST",
      body: JSON.stringify({ question_id: questionId, ...payload }),
    }),
  submitPart2Answer: (attemptId: number, questionId: number, payload: Record<string, unknown>) =>
    request<Record<string, unknown>>(`/attempts/${attemptId}/part2-answer`, {
      method: "POST",
      body: JSON.stringify({ question_id: questionId, ...payload }),
    }),
  uploadSolutionImage: (attemptId: number, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<{ ok: boolean; url: string }>(`/attempts/${attemptId}/solution-image`, { method: "POST", body: form });
  },
  finishPart1: (attemptId: number) => request<{ ok: boolean }>(`/attempts/${attemptId}/finish-part1`, { method: "POST" }),
  finishAttempt: (attemptId: number) => request<import("./types").ResultsView>(`/attempts/${attemptId}/finish`, { method: "POST" }),
  getResults: (attemptId: number) => request<import("./types").ResultsView>(`/attempts/${attemptId}/results`),

  // ---------- планнер ----------
  getMaterials: () => request<{ decks: {id:number;title:string;count:number}[]; quizzes: {id:number;title:string;count:number}[]; certs: {id:number;title:string;count:number}[] }>("/materials", {}, true),
  getPlan: () => request<Record<string, unknown>>("/plan", {}, true),
  createPlan: (data: Record<string, unknown>) => request<{ ok: boolean; plan_id: number }>("/plan", { method: "POST", body: JSON.stringify(data) }, true),
  addPlanItems: (items: unknown[]) => request<{ ok: boolean; added: number }>("/plan/items", { method: "POST", body: JSON.stringify({ items }) }, true),
  deletePlan: (id: number) => request<{ ok: boolean }>("/plan/delete", { method: "POST", body: JSON.stringify({ id }) }, true),
  getDashboard: () => request<Record<string, unknown>>("/dashboard", {}, true),
};
