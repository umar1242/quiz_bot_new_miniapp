import type { Y1Option } from "../../types";

interface Props {
  options: Y1Option[];
  onChange: (options: Y1Option[]) => void;
}

export function Y1Editor({ options, onChange }: Props) {
  function setText(i: number, text: string) {
    onChange(options.map((o, idx) => (idx === i ? { ...o, text } : o)));
  }
  function setCorrect(i: number) {
    onChange(options.map((o, idx) => ({ ...o, is_correct: idx === i })));
  }

  return (
    <div className="field">
      <span className="label">Варианты ответа (отметьте правильный)</span>
      {options.map((opt, i) => (
        <div className="option-row" key={i}>
          <button
            className={`correct-toggle ${opt.is_correct ? "on" : ""}`}
            onClick={() => setCorrect(i)}
            title="Правильный ответ"
          >
            ✓
          </button>
          <input type="text" value={opt.text} onChange={(e) => setText(i, e.target.value)} placeholder={`Вариант ${i + 1}`} />
        </div>
      ))}
    </div>
  );
}
