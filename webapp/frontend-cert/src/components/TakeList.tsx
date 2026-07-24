import type { VariantBrief } from "../types";

interface Props {
  variants: VariantBrief[];
  onTake: (id: number) => void;
  loading: boolean;
}

export function TakeList({ variants, onTake, loading }: Props) {
  // Показываем только готовые к прохождению варианты
  const readyVariants = variants.filter(v => v.status === "ready");

  return (
    <div>
      <h2 style={{ marginBottom: 16 }}>Доступные тесты для прохождения</h2>
      {loading ? (
        <div className="empty-state"><span className="spinner" /></div>
      ) : readyVariants.length === 0 ? (
        <div className="card empty-state">Нет доступных тестов для прохождения.</div>
      ) : (
        <div className="variant-list">
          {readyVariants.map((v) => (
            <div
              className="card variant-row"
              key={v.id}
              onClick={() => onTake(v.id)}
              style={{ cursor: "pointer" }}
            >
              <div className="variant-row-main">
                <span className="variant-row-title">{v.title}</span>
                <span className="variant-row-meta">
                  <span className={`status-dot ready`} />
                  {v.question_count}/43 заданий
                </span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                <button
                  className="btn btn-primary"
                  style={{ padding: "6px 12px", fontSize: "14px" }}
                  onClick={(e) => { e.stopPropagation(); onTake(v.id); }}
                >
                  ▶ Пройти
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
