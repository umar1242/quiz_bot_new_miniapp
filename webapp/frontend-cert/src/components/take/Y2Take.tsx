/**
 * Y2Take — прохождение заданий 33-35:
 * Одно условие (в q.text), 3 подвопроса, для каждого выбрать букву A-F.
 * Варианты A-F приходят в q.options (из CertOption через API).
 * Подвопросы приходят в q.subquestions (из CertMatchPair.left_text через API).
 */
import { useState } from "react";
import { api } from "../../api";
import type { TakeQuestion } from "../../types";

interface Props {
  attemptId: number;
  question: TakeQuestion;
  onAnswered: (patch: Partial<TakeQuestion>) => void;
  onError: (msg: string) => void;
}

const LETTERS = ["A", "B", "C", "D", "E", "F"];

export function Y2Take({ attemptId, question, onAnswered, onError }: Props) {
  const answered = !!question.answered;
  const savedChoices = (question.your_answer?.choices as Record<string, string>) ?? {};

  // {subquestion_id: selected_letter}
  const [choices, setChoices] = useState<Record<number, string>>(() => {
    const init: Record<number, string> = {};
    (question.subquestions ?? []).forEach((sq) => {
      init[sq.id] = savedChoices[String(sq.id)] ?? "";
    });
    return init;
  });

  const [correctChoices, setCorrectChoices] = useState<Record<string, string> | null>(null);
  const [busy, setBusy] = useState(false);

  const subquestions = question.subquestions ?? [];
  const options = question.options ?? [];

  // Все подвопросы выбраны?
  const allChosen = subquestions.every((sq) => choices[sq.id]);

  async function submit() {
    if (answered || busy || !allChosen) return;
    setBusy(true);
    try {
      const choicesPayload: Record<string, string> = {};
      Object.entries(choices).forEach(([k, v]) => { choicesPayload[k] = v; });

      const res = await api.submitAnswer(attemptId, question.id, { choices: choicesPayload });
      setCorrectChoices(res.correct_choices as Record<string, string>);
      onAnswered({
        answered: true,
        your_answer: { choices: choicesPayload },
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
      {/* Таблица вариантов A-F */}
      {options.length > 0 && (
        <div className="y2-options-table">
          <div className="y2-options-legend">
            {options.map((opt, i) => (
              <div key={opt.id} className="y2-opt-item">
                <span className="y2-opt-letter">{LETTERS[i]}</span>
                <span className="y2-opt-text">{opt.text}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Подвопросы */}
      <div className="y2-subqs">
        {subquestions.map((sq, idx) => {
          const selected = choices[sq.id] ?? "";
          const isCorrect = correctChoices ? selected === correctChoices[String(sq.id)] : null;
          return (
            <div key={sq.id} className="y2-subq-take">
              <div className="y2-subq-header">
                <span className="y2-subq-num">{question.number + idx}</span>
              </div>
              <div className="y2-letters-row">
                {LETTERS.map((letter) => {
                  const isSelected = selected === letter;
                  let cls = "y2-letter-btn";
                  if (answered && correctChoices) {
                    const correct = correctChoices[String(sq.id)];
                    if (letter === correct) cls += " correct";
                    else if (isSelected && letter !== correct) cls += " wrong";
                  } else if (isSelected) {
                    cls += " chosen";
                  }
                  return (
                    <button
                      key={letter}
                      className={cls}
                      disabled={answered || busy}
                      onClick={() => !answered && setChoices((c) => ({ ...c, [sq.id]: letter }))}
                    >
                      {letter}
                    </button>
                  );
                })}
                {answered && correctChoices && (
                  <span className={`y2-subq-result ${isCorrect ? "ok" : "bad"}`}>
                    {isCorrect ? "✓" : `✗ → ${correctChoices[String(sq.id)]}`}
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {!answered && (
        <button
          className="btn btn-primary"
          onClick={submit}
          disabled={!allChosen || busy}
          style={{ marginTop: 12 }}
        >
          {busy ? <span className="spinner" /> : "Ответить"}
        </button>
      )}

      {answered && (
        <div className={`feedback-banner ${question.is_correct ? "ok" : "bad"}`}>
          {question.is_correct ? "Все верно" : "Есть ошибки"} · {question.points_earned}/{question.points}
        </div>
      )}
    </div>
  );
}
