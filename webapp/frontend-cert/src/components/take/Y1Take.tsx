import { useState } from "react";
import { api } from "../../api";
import type { TakeQuestion } from "../../types";
import { MarkdownText } from "../MarkdownText";

interface Props {
  attemptId: number;
  question: TakeQuestion;
  onAnswered: (patch: Partial<TakeQuestion>) => void;
  onError: (msg: string) => void;
}

const LETTERS = ["A", "B", "C", "D", "E", "F"];

export function Y1Take({ attemptId, question, onAnswered, onError }: Props) {
  const [busy, setBusy] = useState(false);
  const answered = !!question.answered;
  const chosenId = (question.your_answer?.option_id as number) ?? null;
  const [correctId, setCorrectId] = useState<number | null>(null);

  async function choose(optionId: number) {
    if (answered || busy) return;
    setBusy(true);
    try {
      const res = await api.submitAnswer(attemptId, question.id, { option_id: optionId });
      setCorrectId(res.correct_option_id as number);
      onAnswered({
        answered: true,
        your_answer: { option_id: optionId },
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
      {question.options?.map((opt, i) => {
        const classes = ["choice-btn"];
        const isChosen = chosenId === opt.id;
        if (answered) {
          if (opt.id === correctId) classes.push("correct");
          else if (isChosen) classes.push("wrong");
        } else if (isChosen) classes.push("chosen");
        return (
          <button key={opt.id} className={classes.join(" ")} disabled={answered || busy} onClick={() => choose(opt.id)}>
            <span className="choice-letter">{LETTERS[i]}</span>
            <MarkdownText content={opt.text} className="option-md" />
          </button>
        );
      })}
      {answered && (
        <div className={`feedback-banner ${question.is_correct ? "ok" : "bad"}`}>
          {question.is_correct ? "Верно" : "Неверно"} · {question.points_earned}/{question.points}
        </div>
      )}
    </div>
  );
}
