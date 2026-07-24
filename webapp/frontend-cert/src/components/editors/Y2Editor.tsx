/**
 * Y2Editor — редактор заданий 33-35 (сопоставление нового формата):
 * - 1 общее условие (хранится в question.text, редактируется в QuestionPanel)
 * - 3 подвопроса (pairs[].left = текст, pairs[].right = правильная буква A-F)
 * - 6 вариантов ответа A-F (y2options[].text = расшифровка варианта)
 */
import type { Y2Option, Y2Pair } from "../../types";

const LETTERS = ["A", "B", "C", "D", "E", "F"];

interface Props {
  pairs: Y2Pair[];         // подвопросы (3 шт.)
  y2options: Y2Option[];   // варианты ответа A-F (6 шт.)
  onChange: (pairs: Y2Pair[], y2options: Y2Option[]) => void;
}

export function Y2Editor({ pairs, y2options, onChange }: Props) {
  // Обновить правильный ответ подвопроса (буква A-F)
  function updatePairRight(i: number, letter: string) {
    const updated = pairs.map((p, idx) => (idx === i ? { ...p, right: letter } : p));
    onChange(updated, y2options);
  }

  // Обновить текст варианта ответа A-F
  function updateOption(i: number, value: string) {
    const updated = y2options.map((o, idx) => (idx === i ? { ...o, text: value } : o));
    onChange(pairs, updated);
  }

  return (
    <div>
      {/* Варианты ответа A-F */}
      <div className="field">
        <span className="label">Варианты ответа (A–F)</span>
        <div className="y2-options-grid">
          {LETTERS.map((letter, i) => (
            <div key={letter} className="y2-option-row">
              <span className="y2-letter-badge">{letter}</span>
              <input
                type="text"
                value={y2options[i]?.text ?? ""}
                onChange={(e) => updateOption(i, e.target.value)}
                placeholder={`Вариант ${letter}`}
              />
            </div>
          ))}
        </div>
      </div>

      {/* Подвопросы */}
      <div className="field">
        <span className="label">Подвопросы (33–35) и правильные ответы</span>
        {pairs.map((p, i) => (
          <div key={i} className="y2-subq-row">
            <span className="y2-subq-num">{33 + i}</span>
            <select
              value={p.right}
              onChange={(e) => updatePairRight(i, e.target.value)}
              className="y2-answer-select"
            >
              {LETTERS.map((letter) => (
                <option key={letter} value={letter}>{letter}</option>
              ))}
            </select>
          </div>
        ))}
      </div>
    </div>
  );
}
