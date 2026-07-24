import type { CertQuestion, Progress, QType } from "../types";
import { SECTION_LABELS, SECTION_RANGES } from "../types";

interface Props {
  questions: CertQuestion[];
  progress: Progress;
  selectedId: number | null;
  onSelectQuestion: (q: CertQuestion) => void;
  onAddInSection: (qtype: QType) => void;
}

const SECTION_ORDER: QType[] = ["Y1", "Y2", "O1", "O2"];

export function AnswerSheet({ questions, progress, selectedId, onSelectQuestion, onAddInSection }: Props) {
  const byNumber = new Map(questions.map((q) => [q.number, q]));

  return (
    <div className="card sheet">
      <div className="sheet-progress">
        <div className="sheet-progress-bar">
          <div className="sheet-progress-fill" style={{ width: `${progress.percent}%` }} />
        </div>
        <span className="sheet-progress-pct">{progress.percent}%</span>
      </div>

      {SECTION_ORDER.map((qtype) => {
        const [lo, hi] = SECTION_RANGES[qtype];
        const cells = [];
        for (let n = lo; n <= hi; n++) cells.push(n);

        return (
          <div className="sheet-section" key={qtype}>
            <div className="sheet-section-head">
              <span className="sheet-section-code">
                {qtype} · {lo}–{hi}
              </span>
              <span className="sheet-section-label">{SECTION_LABELS[qtype]}</span>
            </div>
            <div className="sheet-grid">
              {cells.map((n) => {
                const q = byNumber.get(n);
                const classes = ["sheet-cell"];
                if (q?.needs_image) classes.push("needs-image");
                else if (q) classes.push("filled");
                if (q && q.id === selectedId) classes.push("selected");
                if (!q) classes.push("add");

                return (
                  <button
                    key={n}
                    className={classes.join(" ")}
                    onClick={() => (q ? onSelectQuestion(q) : onAddInSection(qtype))}
                    title={q ? q.text.slice(0, 60) : "Добавить задание"}
                  >
                    {n}
                  </button>
                );
              })}
            </div>
          </div>
        );
      })}

      <div className="legend">
        <span className="legend-item"><span className="legend-swatch" style={{ background: "var(--accent-soft)", border: "1px solid var(--accent)" }} /> заполнено</span>
        <span className="legend-item"><span className="legend-swatch" style={{ background: "var(--amber-soft)", border: "1px solid var(--amber)" }} /> нужен рисунок</span>
        <span className="legend-item"><span className="legend-swatch" style={{ background: "var(--surface)", border: "1.5px dashed var(--line)" }} /> пусто</span>
      </div>
    </div>
  );
}
