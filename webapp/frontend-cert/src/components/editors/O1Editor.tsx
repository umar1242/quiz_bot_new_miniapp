import type { O1Answer } from "../../types";

interface Props {
  answers: O1Answer[];
  onChange: (answers: O1Answer[]) => void;
}

export function O1Editor({ answers, onChange }: Props) {
  function update(i: number, patch: Partial<O1Answer>) {
    onChange(answers.map((a, idx) => (idx === i ? { ...a, ...patch } : a)));
  }
  function remove(i: number) {
    onChange(answers.filter((_, idx) => idx !== i));
  }
  function add() {
    onChange([...answers, { text: "", match_mode: "exact", tolerance: null }]);
  }

  return (
    <div className="field">
      <span className="label">Эталонные ответы (принимаются как верные)</span>
      {answers.map((a, i) => (
        <div className="pair-row" key={i}>
          <input type="text" value={a.text} onChange={(e) => update(i, { text: e.target.value })} placeholder="Ответ" />
          <select
            value={a.match_mode}
            onChange={(e) => update(i, { match_mode: e.target.value as "exact" | "numeric" })}
            style={{ padding: "9px 8px", borderRadius: 8, border: "1px solid var(--line)" }}
          >
            <option value="exact">точно</option>
            <option value="numeric">число ± допуск</option>
          </select>
          {a.match_mode === "numeric" && (
            <input
              type="number"
              value={a.tolerance ?? 0}
              onChange={(e) => update(i, { tolerance: Number(e.target.value) })}
              placeholder="±"
              style={{ width: 70 }}
            />
          )}
          <button className="icon-btn" onClick={() => remove(i)} aria-label="Удалить ответ">✕</button>
        </div>
      ))}
      <button className="btn btn-ghost" onClick={add}>+ Добавить эталонный ответ</button>
    </div>
  );
}
