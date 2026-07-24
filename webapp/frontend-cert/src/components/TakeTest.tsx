import { useEffect, useState } from "react";
import { api } from "../api";
import type { AttemptView, ResultsView, TakeQuestion } from "../types";
import { MarkdownText } from "./MarkdownText";
import { O1Take } from "./take/O1Take";
import { O2Take } from "./take/O2Take";
import { ResultsScreen } from "./take/ResultsScreen";
import { Timer } from "./take/Timer";
import { Y1Take } from "./take/Y1Take";
import { Y2Take } from "./take/Y2Take";

interface Props {
  variantId: number;
  initialAttemptId: number | null;
  onBack?: () => void;
}

export function TakeTest({ variantId, initialAttemptId, onBack }: Props) {
  const [attempt, setAttempt] = useState<AttemptView | null>(null);
  const [results, setResults] = useState<ResultsView | null>(null);
  const [idx, setIdx] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  function notifyError(msg: string) {
    setError(msg);
    setTimeout(() => setError(null), 3500);
  }

  async function load(attemptId: number) {
    const v = await api.getAttempt(attemptId);
    setAttempt(v);
    if (v.status === "finished") {
      const r = await api.getResults(attemptId);
      setResults(r);
    }
  }

  useEffect(() => {
    (async () => {
      try {
        let attemptId = initialAttemptId;
        if (!attemptId) {
          const res = await api.startAttempt(variantId);
          attemptId = res.attempt_id;
          const url = new URL(window.location.href);
          url.searchParams.set("attempt", String(attemptId));
          window.history.replaceState({}, "", url.toString());
        }
        await load(attemptId);
      } catch (e) {
        notifyError((e as Error).message);
      } finally {
        setLoading(false);
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function patchQuestion(questionId: number, patch: Partial<TakeQuestion>) {
    setAttempt((a) => (a ? { ...a, questions: a.questions.map((q) => (q.id === questionId ? { ...q, ...patch } : q)) } : a));
  }

  async function handlePart1Expire() {
    if (!attempt) return;
    try {
      await api.finishPart1(attempt.id);
      await load(attempt.id);
      setIdx(0);
    } catch (e) {
      notifyError((e as Error).message);
    }
  }

  async function handlePart2Expire() {
    if (!attempt) return;
    try {
      const r = await api.finishAttempt(attempt.id);
      setResults(r);
      setAttempt((a) => (a ? { ...a, status: "finished" } : a));
    } catch (e) {
      notifyError((e as Error).message);
    }
  }

  async function finishPart1Manually() {
    if (!attempt) return;
    if (!confirm("Завершить тестовую часть и перейти к письменной?")) return;
    await handlePart1Expire();
  }

  async function finishAll() {
    if (!attempt) return;
    if (!confirm("Завершить тест и сдать на проверку?")) return;
    await handlePart2Expire();
  }

  if (loading) return <div className="empty-state"><span className="spinner" /></div>;
  if (!attempt) return <div className="card empty-state">{error || "Не удалось загрузить попытку"}</div>;
  if (results) return <ResultsScreen results={results} />;

  const currentPartQuestions = attempt.questions.filter((q) => (attempt.status === "part1" ? q.part === 1 : q.part === 2));
  const q = currentPartQuestions[idx];

  return (
    <div>
      {onBack && (
        <div style={{ padding: "8px 0 4px" }}>
          <button className="btn back-btn" onClick={onBack}>← Все варианты</button>
        </div>
      )}
      <div className="take-header">
        <span className="take-progress-text">
          {attempt.status === "part1" ? "Тестовая часть" : "Письменная часть"} · {idx + 1}/{currentPartQuestions.length}
        </span>
        {attempt.status === "part1" ? (
          <Timer secondsLeft={attempt.part1_seconds_left} onExpire={handlePart1Expire} />
        ) : (
          <Timer secondsLeft={attempt.part2_seconds_left ?? 0} onExpire={handlePart2Expire} />
        )}
      </div>

      {idx === 0 && attempt.status === "part1" && (
        <div className="take-part-banner">
          Задания 1–40: правильный ответ показывается сразу после вашего выбора. Общий таймер — на всю часть.
        </div>
      )}
      {idx === 0 && attempt.status === "part2" && (
        <div className="take-part-banner">
          Письменная часть: впишите ответы по пунктам и приложите фото полного решения. Баллы за пункты
          считаются автоматически, ход решения оценивается по фото.
        </div>
      )}

      {q && (
        <div className="card q-card">
          <div className="q-number">№{q.number} · {q.points} б.</div>
          {q.images.map((im) => <img className="q-image" key={im.id} src={im.url} alt="" />)}
          <MarkdownText content={q.text} className="q-text" />

          {q.qtype === "Y1" && <Y1Take attemptId={attempt.id} question={q} onAnswered={(p) => patchQuestion(q.id, p)} onError={notifyError} />}
          {q.qtype === "Y2" && <Y2Take attemptId={attempt.id} question={q} onAnswered={(p) => patchQuestion(q.id, p)} onError={notifyError} />}
          {q.qtype === "O1" && <O1Take attemptId={attempt.id} question={q} onAnswered={(p) => patchQuestion(q.id, p)} onError={notifyError} />}
          {q.qtype === "O2" && <O2Take attemptId={attempt.id} question={q} onAnswered={(p) => patchQuestion(q.id, p)} onError={notifyError} />}
        </div>
      )}

      <div className="take-nav">
        <button className="btn" onClick={() => setIdx((i) => Math.max(0, i - 1))} disabled={idx === 0}>← Назад</button>
        {idx < currentPartQuestions.length - 1 ? (
          <button className="btn btn-primary" onClick={() => setIdx((i) => i + 1)}>Далее →</button>
        ) : attempt.status === "part1" ? (
          <button className="btn btn-primary" onClick={finishPart1Manually}>Завершить тестовую часть</button>
        ) : (
          <button className="btn btn-primary" onClick={finishAll}>Сдать тест</button>
        )}
      </div>

      {error && <div className="toast error">{error}</div>}
    </div>
  );
}
