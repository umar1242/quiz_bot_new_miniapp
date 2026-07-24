import { useState } from "react";
import { api } from "../../api";
import type { TakeQuestion } from "../../types";

interface Props {
  attemptId: number;
  question: TakeQuestion;
  onAnswered: (patch: Partial<TakeQuestion>) => void;
  onError: (msg: string) => void;
}

export function O1Take({ attemptId, question, onAnswered, onError }: Props) {
  const answered = !!question.answered;
  const [text, setText] = useState((question.your_answer?.text as string) ?? "");
  const [refs, setRefs] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);

  async function submit() {
    if (answered || busy || !text.trim()) return;
    setBusy(true);
    try {
      const res = await api.submitAnswer(attemptId, question.id, { text });
      setRefs((res.reference_answers as string[]) ?? []);
      onAnswered({
        answered: true,
        your_answer: { text },
        is_correct: res.is_correct as boolean,
        points_earned: res.points_earned as number,
      });
    } catch (e) {
      onError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <input
        type="text"
        value={text}
        onChange={(e) => setText(e.target.value)}
        disabled={answered || busy}
        placeholder="Ваш ответ"
        onKeyDown={(e) => e.key === "Enter" && submit()}
      />
      {!answered && (
        <button className="btn btn-primary" onClick={submit} disabled={!text.trim() || busy} style={{ marginTop: 10 }}>
          {busy ? <span className="spinner" /> : "Ответить"}
        </button>
      )}
      {answered && (
        <div className={`feedback-banner ${question.is_correct ? "ok" : "bad"}`}>
          {question.is_correct ? "Верно" : `Неверно${refs.length ? ` · верный ответ: ${refs.join(", ")}` : ""}`} · {question.points_earned}/{question.points}
        </div>
      )}
    </div>
  );
}
