import type { O2Band } from "../../types";

interface Props {
  bands: O2Band[];
  onChange: (bands: O2Band[]) => void;
}

export function O2Editor({ bands, onChange }: Props) {
  function update(i: number, patch: Partial<O2Band>) {
    onChange(bands.map((b, idx) => (idx === i ? { ...b, ...patch } : b)));
  }
  function remove(i: number) {
    onChange(bands.filter((_, idx) => idx !== i).map((b, idx) => ({ ...b, band_no: idx + 1 })));
  }
  function add() {
    onChange([...bands, { band_no: bands.length + 1, prompt: "", reference_answer: "", match_mode: "numeric", tolerance: 0, max_points: 1 }]);
  }

  const total = bands.reduce((s, b) => s + (b.max_points || 0), 0);

  return (
    <div className="field">
      <span className="label">Пункты (band) — эталонный ответ и балл за каждый · итого {total}</span>
      {bands.map((b, i) => (
        <div className="card" style={{ padding: 10, marginBottom: 8 }} key={i}>
          <div className="band-row">
            <span className="badge">п.{b.band_no}</span>
            <input
              type="text"
              value={b.prompt ?? ""}
              onChange={(e) => update(i, { prompt: e.target.value })}
              placeholder="Что считаем в этом пункте (необязательно)"
            />
            <button className="icon-btn" onClick={() => remove(i)} aria-label="Удалить пункт">✕</button>
          </div>
          <div className="band-row">
            <input
              type="text"
              value={b.reference_answer}
              onChange={(e) => update(i, { reference_answer: e.target.value })}
              placeholder="Эталонный ответ"
            />
            <select
              value={b.match_mode}
              onChange={(e) => update(i, { match_mode: e.target.value as "exact" | "numeric" })}
              style={{ padding: "9px 8px", borderRadius: 8, border: "1px solid var(--line)" }}
            >
              <option value="numeric">число ± допуск</option>
              <option value="exact">точно</option>
            </select>
            {b.match_mode === "numeric" && (
              <input
                type="number"
                value={b.tolerance ?? 0}
                onChange={(e) => update(i, { tolerance: Number(e.target.value) })}
                placeholder="±"
                style={{ width: 60 }}
              />
            )}
            <input
              type="number"
              value={b.max_points}
              onChange={(e) => update(i, { max_points: Number(e.target.value) })}
              placeholder="балл"
              style={{ width: 70 }}
            />
          </div>
        </div>
      ))}
      <button className="btn btn-ghost" onClick={add}>+ Добавить пункт</button>
      <p className="hint">
        Ученик вводит ответ по каждому пункту (проверяется автоматически) и прикладывает фото
        решения целиком — методика и вычисления оцениваются по фото, отдельный балл за них
        конструктор не считает.
      </p>
    </div>
  );
}
